# AgvSimService — Otonom Mobil Robot Simülasyon Servisi

Depo içi palet taşıma süreçlerini (yerleştirme/toplama) AGV/AMR simülasyonu ile canlı görselleştiren sibling FastAPI servisi.

> **Mimari karar:** WMS source-of-truth `BackendProje`'dir. Bu servis **DB yazmaz**, in-memory dünya tutar; görev bitince HTTP callback ile WMS'i günceller.
>
> Detaylı plan: [`../AGV_SIMULATION_PLAN.md`](../AGV_SIMULATION_PLAN.md)

## Hızlı Başlangıç

```bash
cd AgvSimService

# 1) Sanal ortam (ilk kurulum)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2) Bağımlılıklar
pip install -r requirements.txt
pip install -r requirements-test.txt   # test bağımlılıkları

# 3) Ortam değişkenleri
cp .env.example .env                    # değerleri doldurun
# INTERNAL_API_KEY üret: python -c "import secrets; print(secrets.token_hex(32))"
# Aynı değer BackendProje/.env içine de yazılmalı.

# 4) Çalıştır (BackendProje 8000'de çalışırken)
uvicorn main:app --reload --host 127.0.0.1 --port 8002

# Test
pytest                                  # 50+ test
pytest tests/unit                       # sadece unit
```

`http://127.0.0.1:8002/healthz` → servisin ayakta olduğunu doğrular.
`http://127.0.0.1:8002/docs` → OpenAPI dokümantasyonu.

## Ortam Değişkenleri

`.env.example` dosyasına bakın. Zorunlu/önemli olanlar:

| Değişken | Default | Açıklama |
|---|---|---|
| `WMS_BASE_URL` | `http://127.0.0.1:8000` | BackendProje URL'i |
| `INTERNAL_API_KEY` | _(boş)_ | Servisler arası shared secret — BackendProje ile aynı olmalı |
| `TICK_HZ` | `2` | Tick loop frekansı (Hz). 5-10 önerilir; düşük değer daha yavaş simülasyon |
| `CORS_ALLOW_ORIGINS` | `https://localhost:5173` | Frontend origin listesi (virgülle ayır) |
| `GRID_JSON_PATH` | `./data/depo_1_grid.json` | Statik grid kaynağı (Faz 2'de WMS API ile değiştirilebilir) |
| `WS_MAX_QUEUE` | `32` | Yavaş WS client koruması |

## API ve WS Yüzeyi

| Endpoint | Açıklama |
|---|---|
| `GET /healthz` | Sağlık kontrolü |
| `GET /api/agv/grid` | Statik grid (raflar, şarjlar) — frontend ilk açılışta okur |
| `GET /api/agv/robotlar` | Robotların anlık snapshot'ı |
| `POST /api/agv/gorevler` | Görev kabul (BackendProje → AGV; `X-Internal-Api-Key` korumalı) |
| `WS /ws/agv` | Canlı telemetri: ilk mesaj `snapshot`, sonra `delta` (her tick) + `event`'ler |

WS mesaj tipleri: `snapshot`, `delta`, `event` (`gorev_atandi`, `kaynaga_vardi`, `palet_alindi`, `hedefe_vardi`, `palet_birakildi`, `gorev_tamamlandi`, `rota_hesaplandi`, `deadlock_replan`, `deadlock_hata`, `sarja_donuyor`, `sarjda`, `batarya_bitti`, `robot_hata`).

## Önemli Kurallar

- **Tek süreç zorunlu.** Birden fazla worker/instance ile çalıştırılmaz (in-memory world tutarsız olur).
- **DB erişimi yok.** State persist edilmez; restart'ta WMS'ten beklemekte olan görevler yeniden çekilir.
- **Frontend business logic barındırmaz.** Pathfinding, atama, durum geçişleri bu serviste.
- **WMS callback eventual consistency.** Robot LOKAL'de BOS'a dönse de WMS callback başarısızsa görev WMS'te orphan kalabilir; runtime sadece loglar.

## Geliştirme Fazları

- [x] **Faz 0** — İskelet
- [x] **Faz 1** — Tick loop + A* pathfinding + WS broadcast
- [x] **Faz 2** — Frontend MVP (Three.js sahnesi, zustand, useFrame interp.)
- [x] **Faz 3** — WMS entegrasyonu (dispatcher hook + `/api/agv-callbacks/gorev-tamamlandi`)
- [x] **Faz 4** — Çoklu robot (4 AGV) + cooperative-light A* (reservation table) + deadlock recovery + click-to-select
- [x] **Faz 5** — Cilalama (batarya simülasyonu + otonom şarja dönüş, aktif görev paneli, dokümantasyon)

## Mimari Akış (Özet)

```
WMS yerleştirme görevi olur (BackendProje)
   ↓ HttpAgvDispatcher (feature flag açıksa, fire-and-forget)
POST /api/agv/gorevler (X-Internal-Api-Key)
   ↓ AGV görevi kuyruğa, GorevAtamaUseCase boş robota atar
TickUseCase robotu KAYNAK→YÜKLE→TAŞI→BIRAK→TAMAMLANDI_BILDIRIM ilerletir
   ↓ TickLoop event'ten WMS callback üretir (background asyncio task)
POST /api/agv-callbacks/gorev-tamamlandi (BackendProje)
   ↓ AgvYerlestirmeTamamlaUseCase (state zorla DEVAM_EDIYOR + tamamla UC delegate)
WMS'te palet konum + mal kabul kapanma + LMS performans event yazılır
```

## Test Stratejisi

- `tests/unit/test_grid.py`, `test_pathfinding.py`, `test_pathfinding_cooperative.py`, `test_robot_state.py`, `test_deadlock.py`, `test_batarya.py`, `test_world_tick.py` — saf birim testler.
- `tests/integration/test_gorev_kabul_endpoint.py`, `test_multi_robot.py` — TestClient + 4 robot smoke trafiği.
- `pytest.ini` `pythonpath=., asyncio_mode=auto`.

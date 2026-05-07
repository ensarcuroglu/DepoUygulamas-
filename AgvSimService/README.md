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

# 4) Çalıştır (BackendProje 8000'de çalışırken)
uvicorn main:app --reload --host 127.0.0.1 --port 8002
```

`http://127.0.0.1:8002/healthz` → servisin ayakta olduğunu doğrular.
`http://127.0.0.1:8002/docs` → OpenAPI dokümantasyonu.

## Ortam Değişkenleri

`.env.example` dosyasına bakın. Zorunlu olanlar:

| Değişken | Açıklama |
|---|---|
| `WMS_BASE_URL` | BackendProje URL'i (default: `http://127.0.0.1:8000`) |
| `INTERNAL_API_KEY` | Servisler arası shared secret — **BackendProje ile aynı olmalı** |
| `TICK_HZ` | Tick loop frekansı (default: `5`) |
| `CORS_ALLOW_ORIGINS` | Frontend origin listesi |

## Proje Yapısı (Faz 0)

```
AgvSimService/
├── main.py              # FastAPI app + healthz
├── config.py            # pydantic-settings
├── requirements.txt
├── requirements-test.txt
├── .env.example
├── app/
│   ├── core/            # Domain (Faz 1+: robot, grid, pathfinding)
│   ├── application/     # Use case'ler (Faz 1+)
│   ├── infrastructure/  # WMS client, WS broadcaster (Faz 1+)
│   ├── api/             # Router'lar (Faz 1+)
│   └── runtime/         # Tick loop (Faz 1+)
└── tests/               # pytest
```

## Önemli Kurallar

- **Tek süreç zorunlu.** Birden fazla worker/instance ile çalıştırılmaz (in-memory world tutarsız olur).
- **DB erişimi yok.** State persist edilmez; restart'ta WMS'ten beklemekte olan görevler yeniden çekilir.
- **Frontend business logic barındırmaz.** Pathfinding, atama, durum geçişi bu serviste.

## Geliştirme Fazları

- **Faz 0** (mevcut) — İskelet
- **Faz 1** — Tick loop + A* pathfinding + WS broadcast
- **Faz 2** — Frontend MVP (Three.js sahnesi)
- **Faz 3** — WMS entegrasyonu (dispatcher + callback)
- **Faz 4** — Çoklu robot + cooperative çakışma önleme
- **Faz 5** — Cilalama (batarya, bağlantı durumu UI, dokümantasyon)

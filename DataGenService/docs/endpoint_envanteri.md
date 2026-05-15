# Faz 0 — Backend Endpoint Envanteri & RabbitMQ Topoloji Tespiti

Faz 4–6 senaryolarının yayın hedeflerini sabitlemek için tarama. Kaynak: `BackendProje/app/api/v1/routers/` (commit: `main`@`2026-05-15`).

## 0. KRİTİK BULGU — Auth Sözleşmesi Çatışması

Plan'da "API ile haberleşirken `INTERNAL_API_KEY` sözleşmesi kullanılmalıdır" yazıyor; ancak mevcut backend'de:

| Endpoint Grubu | Auth Mekanizması | Kaynak |
|---|---|---|
| CRUD (ürün, raf, palet, lot, sipariş, görev, …) | **JWT Bearer** (`get_current_user` / `require_role`) | `app/core/auth.py` |
| Servisler arası callback (agv, belge_taslaklari, excel_ai) | **`X-Internal-Api-Key`** | `app/api/v1/internal_auth.py` |

> **Sonuç:** DataGenService veri basacağı CRUD uçlarında `X-Internal-Api-Key` ile kabul görmez. İki seçenek:
>
> 1. **JWT yolu:** DataGenService başlangıçta `/api/auth/login` (admin user) ile token alır, `Authorization: Bearer <token>` ile basar. Token refresh akışı eklenir. **MVP için önerilen.**
> 2. **Internal yolu:** Backend tarafında seed/load için yeni bir `/api/internal/*` router grubu açılır (`internal_api_key_verify` dependency'si ile). Bu kapsam genişlemesidir.
>
> **Faz 4 başlamadan önce karar verilmeli** — varsayılan: **JWT yolu**. CLAUDE.md "INTERNAL_API_KEY sözleşmesi" ifadesinin servisler arası callback'lere referans olduğu yorumlanıyor; veri üretimi için JWT akışı kabul edilebilir.

---

## 1. Endpoint Envanteri (Yazma Uçları)

### 1.1 Referans Havuz (seed_baseline öncelikli)

| Resource | Method | Path | DTO | Auth | Idempotency-Key |
|---|---|---|---|---|---|
| Ürün | POST | `/api/urunler/` | `UrunCreateDTO` | JWT `admin` | ❌ |
| Ürün | PUT | `/api/urunler/{urun_id}` | `UrunUpdateDTO` | JWT `admin` | ❌ |
| Kategori | POST | `/api/kategoriler/` | `KategoriCreateDTO` | JWT `admin` | ❌ |
| Marka | POST | `/api/markalar/` | `MarkaCreateDTO` | JWT `admin` | ❌ |
| Tedarikçi | POST | `/api/tedarikciler/` | `TedarikciCreateDTO` | JWT `admin` | ❌ |
| Depo | POST | `/api/depolar/` | `DepoCreateDTO` | JWT `admin, lojistik` | ❌ |
| Zon | POST | `/api/zonlar/` | `ZonCreateDTO` | JWT `admin, lojistik` | ❌ |
| Raf | POST | `/api/raflar/` | `RafCreateDTO` | JWT `admin, lojistik` | ❌ |

### 1.2 Stok & Palet (seed_baseline + task_load)

| Resource | Method | Path | DTO | Auth | Idempotency-Key |
|---|---|---|---|---|---|
| Palet (CRUD) | POST | `/api/paletler/` | `PaletCreateDTO` | JWT `admin` | ❌ |
| Lot (CRUD) | POST | `/api/lotlar/` | `LotCreateDTO` | JWT `admin` | ❌ |
| Palet giriş (stok) | POST | `/api/stok-islemleri/palet-giris` | `PaletGirisDTO` | JWT `admin, depocu, lojistik` | ✅ `palet_giris` |
| Palet çıkış (stok) | POST | `/api/stok-islemleri/palet-cikis` | `PaletCikisDTO` | JWT `admin, depocu, lojistik` | ✅ `palet_cikis` |
| Toplu giriş | POST | `/api/stok-islemleri/toplu-giris` | `TopluGirisDTO` | JWT `admin, depocu, lojistik` | ❌ |
| Toplu çıkış | POST | `/api/stok-islemleri/toplu-cikis` | `TopluCikisDTO` | JWT `admin, depocu, lojistik` | ❌ |
| Üretim paleti oluştur | POST | `/api/uretim-paletleri/` | `UretimPaletiCreateDTO` | JWT | ❌ |
| Üretim paleti kabul | POST | `/api/uretim-paletleri/{palet_no}/kabul-et` | — | JWT | ✅ `uretim_paleti_kabul_et` |
| Üretim paleti yerleştir | POST | `/api/uretim-paletleri/{palet_no}/yerlestir` | — | JWT | ✅ `uretim_paleti_yerlestir` |
| Mal kabul (irsaliye) | POST | `/api/mal-kabul/...` | `MalKabulDTO` | JWT `admin, lojistik, depocu` | ✅ |
| Mal kabul irsaliyesi | POST | `/api/mal-kabul-irsaliyeleri/` | `MalKabulIrsaliyeCreateDTO` | JWT `admin, depocu` | ❌ |

### 1.3 Siparişler

| Resource | Method | Path | DTO | Auth | Idempotency-Key |
|---|---|---|---|---|---|
| Sipariş oluştur | POST | `/api/siparisler/` | `SiparisCreateDTO` | JWT `admin, lojistik` | ❌ |
| Sipariş güncelle | PUT | `/api/siparisler/{siparis_id}` | `SiparisUpdateDTO` | JWT `admin, lojistik` | ❌ |

### 1.4 Görev Akışı (task_load + agv_traffic)

| Resource | Method | Path | DTO | Auth | Idempotency-Key |
|---|---|---|---|---|---|
| Yerleştirme görevi oluştur | POST | `/api/yerlestirme-gorevleri/` | `YerlestirmeGoreviCreateDTO` | JWT `admin, lojistik` | ❌ |
| Yerleştirme sıradaki al | POST | `/api/yerlestirme-gorevleri/siradaki-al` | — | JWT `admin, depocu, lojistik` | ❌ |
| Yerleştirme başlat | POST | `/api/yerlestirme-gorevleri/{gorev_id}/baslat` | — | JWT `admin, depocu, lojistik` | ❌ |
| Yerleştirme tamamla | POST | `/api/yerlestirme-gorevleri/{gorev_id}/tamamla` | `YerlestirmeTamamlaDTO` | JWT `admin, depocu, lojistik` | ❌ |
| Yerleştirme iptal | POST | `/api/yerlestirme-gorevleri/{gorev_id}/iptal` | — | JWT `admin, lojistik` | ❌ |
| Toplama görevi üret | POST | `/api/v1/toplama-gorevleri/uret` | `ToplamaGoreviUretDTO` | JWT `admin, lojistik` | ✅ `gorev_uret` |
| Toplama sıradan al | POST | `/api/v1/toplama-gorevleri/sira-al` | — | JWT `admin, depocu, lojistik` | ✅ `siradan_gorev_al` |
| Toplama başlat | POST | `/api/v1/toplama-gorevleri/{gorev_id}/baslat` | — | JWT `admin, depocu, lojistik` | ❌ |
| Toplama tamamla | POST | `/api/v1/toplama-gorevleri/{gorev_id}/tamamla` | `ToplamaTamamlaDTO` | JWT `admin, depocu, lojistik` | ❌ |
| Toplama iptal | POST | `/api/v1/toplama-gorevleri/{gorev_id}/iptal` | — | JWT `admin, depocu, lojistik` | ❌ |
| Terminal yerleştir (mobil) | POST | `/api/terminal/yerlestir` | `TerminalYerlestirmeDTO` | JWT `admin, depocu, lojistik` | ✅ `terminal_yerlestir` |

### 1.5 Servisler Arası (X-Internal-Api-Key ile — referans)

| Resource | Method | Path | Notlar |
|---|---|---|---|
| AGV callback | POST | `/api/agv-callbacks/gorev-tamamlandi` | AGV servisinden çağrılır; DataGenService **kullanmamalı** (kapsam dışı kararı). |
| Belge taslakları | POST | `/api/belge-taslaklari/...` | DocAi callback; ilgisiz. |
| Excel AI | POST | `/api/excel-ai/...` | ExcelAi proxy; ilgisiz. |

---

## 2. RabbitMQ Topolojisi (task_load için)

Kaynak: `BackendProje/app/infrastructure/messaging/topology.py`, `docs/agent/rabbitmq-operations.md`.

| Parametre | Değer |
|---|---|
| **Exchange** | `depo.events` (topic, durable) |
| **Routing key prefix** | `lms.gorev_performans` |
| **Routing key formatı** | `lms.gorev_performans.<event_tipi>` |
| **Queue binding** | `lms.gorev_performans.*` |
| **Hedef queue** | `depo.lms.operator_metrikleri` (durable, DLX'li) |
| **DLX** | `depo.events.dlx` (topic, durable) |
| **DLQ** | `depo.lms.operator_metrikleri.dlq` |
| **Mesaj** | `delivery_mode=2` (persistent), publisher confirm, mandatory |

### Geçerli `event_tipi` değerleri (`PerformansEventTipi`)

- `GOREV_BASLATILDI`
- `GOREV_TAMAMLANDI`
- `GOREV_IPTAL`

### Geçerli `gorev_tipi` değerleri (`PerformansGorevTipi`)

- `yerlestirme`
- `toplama`

### `GorevPerformansEvent` payload alanları (consumer beklentisi)

```
event_uuid: str         # idempotency anahtarı (UUID4)
event_tipi: str         # GOREV_BASLATILDI | GOREV_TAMAMLANDI | GOREV_IPTAL
gorev_tipi: str         # yerlestirme | toplama
gorev_id: int
kullanici_id: int
depo_id: int | None
sure_saniye: int | None # yalnız GOREV_TAMAMLANDI
iptal_nedeni: str | None# yalnız GOREV_IPTAL
payload: dict | None
olusturma_tarihi: datetime
```

> **Not:** Consumer (`operator_performans_consumer.py`) mesajdaki `event_id` ile **DB'den** `gorev_performans_eventleri` satırını okur. Yani saf event yayını yeterli değildir; consumer DB'de event'i bulamazsa DLQ'ya atar. `task_load --target=rabbit` senaryosu için **DB'ye outbox satırı önce yazılmalı** ya da senaryo `--target=rest` üzerinden use case'leri tetiklemeli (doğal outbox akışı).
>
> **Karar:** `task_load --target=rabbit` MVP'de yalnız "saf yük testi" olarak işaretlenir; consumer'da DLQ artışı beklenir. **Anlamlı LMS yükü için `--target=rest` tercih edilmeli.** Bu, Faz 5 doğrulamasında belirtildi.

---

## 3. AGV → Yerleştirme Akış Bağlantısı (agv_traffic senaryosu)

Kaynak: `docs/agent/backend-notes.md`, `app/infrastructure/services/http_agv_dispatcher.py`, `app/api/v1/routers/agv_callbacks.py`.

```
DataGenService                Backend                            AgvSimService
─────────────                ───────                            ─────────────
POST /api/yerlestirme-gorevleri/  →  YerlestirmeGoreviUseCase
                                          │
                                          ▼ (AGV uygunsa)
                                     HttpAgvDispatcher  ─POST→  /api/v1/gorevler (AGV)
                                                                       │
                                                                       ▼
                                                                  (AGV simülasyonu)
                                                                       │
                                          ◀────── POST /api/agv-callbacks/gorev-tamamlandi
                                          │       (X-Internal-Api-Key)
                                          ▼
                                     AgvYerlestirmeTamamlaUseCase  → WMS state güncellenir
```

**Karar (rev. 1'de sabitlenmişti):** `agv_traffic` senaryosu **yalnız `/api/yerlestirme-gorevleri/` POST eder**. AgvSim'e ne doğrudan istek atar, ne de `/api/agv-callbacks/*` çağırır. WMS kendi `HttpAgvDispatcher`'ı üzerinden AGV'yi tetikler; callback'i AgvSim üretir.

---

## 4. Senaryo × Hedef Uç Haritası

| Senaryo | Hedef Uçlar | Yöntem | Idempotency |
|---|---|---|---|
| `seed_baseline` | kategoriler, markalar, tedarikciler, depolar, zonlar, raflar, ürünler, paletler, lotlar | REST (JWT) | UUID4 `Idempotency-Key`, destekleyen uçlarda kullanılır (palet-giris, vb.) |
| `task_load` (rest) | siparişler → toplama-gorevleri/uret → yerleştirme-gorevleri → tamamla | REST (JWT) | `gorev_uret`, `siradan_gorev_al` |
| `task_load` (rabbit) | `depo.events` × `lms.gorev_performans.*` | aio-pika | `event_uuid` mesaj içinde |
| `timeseries_history` (file) | `ml_models/talep_tahmin/data/raw/talep_gecmis_*.parquet` | Dosya | — |
| `timeseries_history` (rest, opt) | siparişler (geriye dönük) | REST (JWT) | — |
| `agv_traffic` | `/api/yerlestirme-gorevleri/` (POST) | REST (JWT) | — |

---

## 5. Faz 0 Çıktıları (Tamamlandı)

- [x] Backend yazma uçları listelendi (5 grup, ~25 endpoint).
- [x] `Idempotency-Key` destekleyenler işaretlendi (6 uç: palet-giris, palet-cikis, uretim_paleti_kabul_et/yerlestir, gorev_uret, siradan_gorev_al, terminal_yerlestir, mal_kabul).
- [x] RabbitMQ topolojisi (exchange, routing key formatı, queue, DLX/DLQ, persistent + confirm) doğrulandı.
- [x] Geçerli `event_tipi` / `gorev_tipi` enum değerleri çıkarıldı.
- [x] AGV trafik akışı doğrulandı; AgvSim'e doğrudan dokunmama kuralı kaynak kodla teyit edildi.
- [x] **Kritik bulgu**: Auth sözleşmesi çatışması raporlandı (JWT vs X-Internal-Api-Key).
- [x] Senaryo × hedef uç haritası çıkarıldı.

## 6. Faz 1 Başlamadan Önce Cevaplanmalı

1. **Auth kararı:** DataGenService JWT (admin user login) mu kullanacak yoksa backend'e `/api/internal/*` seed router'ı mı eklensin? → MVP için **JWT** öneriliyor.
2. **`task_load --target=rabbit` semantiği:** Saf yük testi (DLQ artışı beklenir) mi yoksa Faz 1 kapsamından çıkarılsın mı? Anlamlı LMS yükü için zaten `--target=rest` mevcut.

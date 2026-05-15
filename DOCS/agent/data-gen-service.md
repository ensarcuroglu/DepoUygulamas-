# DataGenService Runbook

DataGenService, WMS ekosistemi icin deterministik sentetik veri ureten FastAPI
servisi ve Typer CLI aracidir. Veritabanina dogrudan yazmaz; sistemin is
kurallarini korumak icin Backend REST API, `depo.events` RabbitMQ exchange'i
veya ML dosya ciktilari uzerinden calisir.

## Servis

- Klasor: `DataGenService/`
- Compose servisi: `data-gen`
- Port: `8005`
- Health: `GET /healthz`
- API: `POST /scenarios/{name}/run`
- CLI: `python -m datagen run <scenario>`

```bash
docker compose up -d data-gen
curl http://localhost:8005/healthz
```

Beklenen health cevabi:

```json
{"status":"ok","service":"data-gen"}
```

## Auth ve Yazma Yolu

REST hedefleri icin DataGenService admin kullanici ile Backend'e login olur:

- `BACKEND_BASE_URL=http://backend:8000`
- `DATAGEN_ADMIN_USERNAME=admin`
- `DATAGEN_ADMIN_PASSWORD=admin123`
- `JWT_REFRESH_BUFFER_SEC=60`

CRUD endpoint'lerinde `X-Internal-Api-Key` kullanilmaz. Bu karar
`DataGenService/docs/endpoint_envanteri.md` icinde sabittir: CRUD uclari JWT
Bearer ister, internal key yalniz servis callback/proxy uclari icindir.

## Senaryo Katalogu

| Senaryo | Varsayilan target | Amac | Not |
|---|---|---|---|
| `seed_baseline` | `rest` | Raf, urun, lot ve palet referans verisi basar | Backend'de kategori/marka/tedarikci/depo/zon seed'i gerekir |
| `task_load` | `rest` | Toplama gorevi veya LMS performans eventi yuku uretir | `rabbit` saf broker/DLQ yuk testidir |
| `timeseries_history` | `file` | Talep tahmin modeli icin gecmis talep serisi uretir | DB'ye dokunmayan en guvenli akistir |
| `agv_traffic` | `rest` | Backend yerlestirme gorevi trafigi uretir | AgvSimService'e dogrudan cagrisi yoktur |

## Target Matrisi

| Senaryo | `rest` | `rabbit` | `file` |
|---|:---:|:---:|:---:|
| `seed_baseline` | evet | hayir | hayir |
| `task_load` | evet | evet | hayir |
| `timeseries_history` | evet, opsiyonel | hayir | evet |
| `agv_traffic` | evet | hayir | hayir |

Izinsiz kombinasyonlar API'de `422 Unprocessable Entity`, CLI'da exit code
`2` ile reddedilir.

## API Kullanimi

Tum senaryolar ayni body yuzeyini kullanir:

```json
{
  "count": 100,
  "seed": 42,
  "target": "file",
  "batch_size": 500,
  "concurrency": 10
}
```

Ornekler:

```bash
curl -X POST http://localhost:8005/scenarios/timeseries_history/run \
  -H "Content-Type: application/json" \
  -d "{\"count\":10,\"seed\":42,\"target\":\"file\",\"batch_size\":500,\"concurrency\":10}"

curl -X POST http://localhost:8005/scenarios/task_load/run \
  -H "Content-Type: application/json" \
  -d "{\"count\":200,\"target\":\"rabbit\"}"
```

Donen ozet:

```json
{
  "scenario": "timeseries_history",
  "output_path": "/workspace/ml_models/talep_tahmin/data/raw/talep_gecmis_20240101_seed42_u10_g30.parquet",
  "total": 300,
  "success": 300,
  "failed": 0,
  "duration_sec": 0.12,
  "p95_latency_ms": 10.4,
  "errors": []
}
```

## CLI Kullanimi

Compose icinde:

```bash
docker compose exec data-gen python -m datagen info
docker compose exec data-gen python -m datagen run timeseries_history --count 10 --target file
docker compose exec data-gen python -m datagen run task_load --count 200 --target rabbit
docker compose exec data-gen python -m datagen run agv_traffic --count 500 --target rest
```

Manuel local:

```bash
cd DataGenService
pip install -r requirements-test.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8005
python -m datagen run timeseries_history --count 10 --target file
```

## Hacim ve Throttle

Varsayilanlar `infra/env/dev.env` icinde tanimlidir:

- `BATCH_SIZE=500`
- `CONCURRENCY=10`
- `HTTP_TIMEOUT_SEC=30`
- `HTTP_MAX_RETRIES=3`
- `DEFAULT_SEED=42`

`count` semantigi:

- `task_load` ve `agv_traffic`: dogrudan kayit/gorev sayisi.
- `timeseries_history`: urun sayisi. Varsayilan gun sayisi 30 oldugu icin
  toplam satir `count * 30` olur.
- `seed_baseline`: toplam seed olcegi. Runner bu sayiyi raf/urun/lot/palet
  default oranlarina boler.

## ML Dosya Ciktisi

`timeseries_history --target=file` varsayilan olarak su dizine yazar:

```text
ml_models/talep_tahmin/data/raw/
```

Compose icinde env:

```text
OUTPUT_DIR=/workspace/ml_models/talep_tahmin/data/raw
```

Parquet dosya adi deterministiktir:

```text
talep_gecmis_YYYYMMDD_seed{seed}_u{urun_count}_g{gun_sayisi}.parquet
```

Beklenen kolonlar:

| Kolon | Tip/icerik |
|---|---|
| `urun_id` | Urun referans id |
| `urun_kodu` | Sentetik urun kodu |
| `tarih` | Talep tarihi |
| `talep_miktari` | Gunluk talep |
| `haftanin_gunu` | 0-6 |
| `promosyon_var` | bool |
| `mevsim_katsayisi` | float |

## RabbitMQ Notlari

`task_load --target=rabbit`, `depo.events` exchange'ine
`lms.gorev_performans.<event_tipi>` routing key'i ile mesaj yayinlar.

Bu mod anlamli LMS aggregator yuku degil, saf broker/DLQ yuk testidir.
Consumer mesajdaki event id ile DB outbox satiri aradigi icin DB'de karsiligi
olmayan sentetik event'lerin DLQ'ya dusmesi beklenen davranistir. Anlamli LMS
yuku icin `task_load --target=rest` kullanin.

## AGV Backend-Only Kurali

`agv_traffic`, yalniz Backend'in yerlestirme gorevi ucuna istek atar:

```text
POST /api/yerlestirme-gorevleri/
```

DataGenService asla AgvSimService portu `8002` veya
`/api/agv-callbacks/*` uclarina dogrudan istek atmaz. WMS state butunlugu icin
AGV tetikleme sorumlulugu Backend'de kalir.

## Dogrulama

```bash
cd DataGenService
pytest -m unit
ruff check .
```

Compose smoke:

```bash
docker compose up -d data-gen
curl http://localhost:8005/healthz
docker compose exec data-gen python -m datagen run timeseries_history --count 5 --target file
```

## Sorun Giderme

| Belirti | Olası neden | Cozum |
|---|---|---|
| REST senaryolari `401`/login hatasi | Admin credential yanlis veya backend seed calismadi | `backend-init` loglarini kontrol edin; dev default `admin/admin123` |
| `target izinli değil` | Senaryo/target matrisi ihlali | Yukaridaki matrise gore target secin |
| RabbitMQ baglanamiyor | `rabbitmq` saglikli degil veya URL yanlis | `docker compose ps rabbitmq`; `RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/` |
| Parquet dosyasi yok | `target=file` degil veya output dizini farkli | `OUTPUT_DIR` ve JSON `output_path` alanini kontrol edin |
| AGV sim logunda dogrudan DataGen istegi var | Kural ihlali | `agv_traffic` implementasyonunu durdurup testleri calistirin |


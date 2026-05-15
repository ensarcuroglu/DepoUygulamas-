# DataGenService

Sentetik depo verisi üretici mikroservis ve CLI. WMS API'lerine (JWT) ve `depo.events` RabbitMQ exchange'ine veri besler; ML eğitim verisini dosyaya yazar.

Plan: `DOCS/DATA_GEN_SERVICE_ENTEGRASYON_PLANI.md`
Endpoint envanteri: `DataGenService/docs/endpoint_envanteri.md`

## Hızlı Başlangıç

```bash
cd DataGenService
pip install -r requirements-test.txt

# FastAPI servisi
uvicorn main:app --reload --host 127.0.0.1 --port 8005

# CLI
python -m datagen --help

# Testler
pytest -m unit
```

Compose içinden:

```bash
docker compose up -d data-gen
docker compose exec data-gen python -m datagen run timeseries_history --count 10 --target file
```

## Sağlık Kontrolü

```bash
curl http://localhost:8005/healthz
# {"status":"ok","service":"data-gen"}
```

## Ortam Değişkenleri

`DataGenService/.env` (örnek `.env.example` ileriki fazlarda eklenecek).

| Değişken | Default | Açıklama |
|---|---|---|
| `BACKEND_BASE_URL` | `http://127.0.0.1:8000` | WMS Backend tabanı |
| `DATAGEN_ADMIN_USERNAME` | — | Admin user (JWT login) |
| `DATAGEN_ADMIN_PASSWORD` | — | Admin user şifresi |
| `JWT_REFRESH_BUFFER_SEC` | `60` | Token refresh tampon süresi |
| `RABBITMQ_URL` | `amqp://guest:guest@127.0.0.1:5672/` | RabbitMQ AMQP URI |
| `DEFAULT_SEED` | `42` | Factory seed |
| `LOCALE` | `tr_TR` | Faker locale |
| `OUTPUT_DIR` | `../ml_models/talep_tahmin/data/raw` | Dosya çıktı dizini |
| `BATCH_SIZE` | `500` | REST batch boyutu |
| `CONCURRENCY` | `10` | `asyncio.Semaphore` limiti |

Detaylı runbook: `DOCS/agent/data-gen-service.md`.

## Port

`8005` (host + compose).

## Faz Durumu

- [x] Faz 0 — Discovery
- [x] Faz 1 — Servis iskeleti
- [x] Faz 2 — Factory katmanı
- [x] Faz 3 — file_emitter + timeseries_history
- [x] Faz 4 — rest_emitter + seed_baseline
- [x] Faz 5 — rabbit_emitter + task_load
- [x] Faz 6 — agv_traffic
- [x] Faz 7 — API + CLI konsolidasyonu
- [ ] Faz 8 — Compose + docs + commit

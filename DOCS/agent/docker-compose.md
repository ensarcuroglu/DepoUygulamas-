# Docker Compose Dev Stack

Repo kökündeki `compose.yml` yerel geliştirme giriş noktasıdır. Compose project name sabit: `depo-dev`.

## Komutlar

```bash
# Stack baslat
docker compose up -d

# Ilk kurulum / dependency degisiklikleri
docker compose up --build

# Durum ve log
docker compose ps
docker compose logs -f backend
docker compose logs -f doc-ai
docker compose logs -f excel-ai

# Stack durdur
docker compose down

# Temiz dev DB (volume dahil sifirla)
docker compose down -v --remove-orphans
docker compose up -d

# Ollama'yi container icinde calistir (opsiyonel)
docker compose -f compose.yml -f compose.ollama.yml up -d
docker compose -f compose.yml -f compose.ollama.yml exec ollama ollama pull qwen2.5-coder:7b
docker compose -f compose.yml -f compose.ollama.yml exec ollama ollama pull qwen3-vl:4b
```

Disk notu: Varsayilan dev akisi host Ollama kullanir; temiz build icin `compose.ollama.yml`
ekleme. Container icindeki Ollama modelleri `ollama_data` volume'unde tutulur ve Docker
VHDX boyutunu hizla buyutebilir.

## Sağlık Kontrol Adresleri

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000` (docs `/docs`)
- WMS AI: `http://localhost:8001/health`
- AGV: `http://localhost:8002/healthz`
- Doc AI: `http://localhost:8003/healthz`
- Excel AI: `http://localhost:8004/healthz`
- RabbitMQ Management: `http://localhost:15672` (`guest`/`guest`)

## RabbitMQ + Backend-Worker

- `rabbitmq` servisi `rabbitmq:3-management` imajını kullanır; AMQP 5672, Mgmt UI 15672. Volume: `rabbitmq_data`.
- `backend-worker` servisi backend ile aynı image'ı kullanır; entry: `python -m app.infrastructure.messaging.operator_performans_consumer`. `RABBITMQ_ENABLED=false` iken boş döngüde bekler (`restart: unless-stopped` ile container ayakta kalır).
- Runtime mode değişikliği: `infra/env/dev.env` içindeki `RABBITMQ_ENABLED` güncelle, ardından `docker compose up -d backend backend-worker` ile recreate. Detay: `docs/agent/rabbitmq-operations.md`.

## Kurallar ve Gotchas

- **Proje klasörü ASCII olmalı:** `D:\Ensar Dosya\DepoUygulamasi`. Türkçe karakterli eski path'leri dokümana / tooling'e geri ekleme.
- **Tracked dev env:** `infra/env/dev.env`. Kişisel secret/override → `infra/env/*.local` veya `infra/env/*.secret` (git'e alınmaz).
- **Fresh dev DB bootstrap:** `backend-init` yapar — `python seed.py && alembic stamp head && python seed_agv_user.py`. Bu sadece local dev kolaylığı; gerçek migration değişikliklerinde Alembic kuralını bozma.
- **`ai-views`** servisi `WmsAiService/views.sql` dosyasını MySQL'e uygular ve çıkar. `backend-init` ve `ai-views` için `Exited` başarılı durum olabilir.
- **Watcher çakışmaları:** Bind mount nedeniyle cache/venv klasörleri runtime watcher'a takılabilir. `.dockerignore`, `WATCHFILES_IGNORE_PERMISSION_DENIED=true` ve `--reload-exclude` ayarlarını koru.
- **Servis ikileme yasak:** Compose çalışırken aynı servisleri ayrıca `uvicorn` ile başlatma; port çakışması olur.

## Vite Dev Server (Compose içi)

- Compose dev varsayılanı HTTP: `http://localhost:5173` (`VITE_DEV_HTTPS=false`).
- Manuel local çalışırken `VITE_DEV_HTTPS=true` ile mkcert/HTTPS kullanılabilir.
- `/api` istekleri `VITE_BACKEND_PROXY_TARGET` ile yönlendirilir. Compose hedefi: `http://backend:8000`. Manuel local: `http://127.0.0.1:8000`.
- `server.host: true` — LAN erişimi açık.
- Build chunk'ları elle bölünmüş: `react-vendor`, `chart-vendor`, `excel-vendor`, `pdf-vendor`, `barcode-vendor`, `ui-vendor`.

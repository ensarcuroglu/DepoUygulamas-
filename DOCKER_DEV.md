# Docker Compose Dev Ortami

Bu compose yapisi local gelistirme konforu icindir. Production hardening, secrets manager, TLS termination ve replica/cluster davranislari bu dosyalarin kapsami disindadir.

## Servisler

- `mysql`: MySQL 8.4, container icinde `mysql:3306`, hostta `localhost:3307`
- `backend`: FastAPI WMS API, `http://localhost:8000`
- `frontend`: Vite dev server, `http://localhost:5173`
- `wms-ai`: LangChain + Ollama AI sorgu servisi, `http://localhost:8001`
- `agv-sim`: AGV/AMR simulasyon servisi, `http://localhost:8002`
- `doc-ai`: Belge AI servisi, `http://localhost:8003`
- `backend-init`: migration + seed one-shot servisi
- `ai-views`: WmsAiService read-only view one-shot servisi

## Ilk Calistirma

Docker Desktop calisir durumdayken:

```bash
docker compose up --build
```

Temiz sifirdan kurulum icin:

```bash
docker compose down -v
docker compose up --build
```

MySQL host makinede `localhost:3307` uzerinden erisilebilir. Container servisleri birbirine Docker network icinden servis adlariyla baglanir.

## Ollama

Varsayilan compose, Ollama'yi host makinede bekler:

```bash
ollama pull qwen2.5-coder:7b
ollama pull qwen3-vl:4b
ollama serve
```

Host Ollama URL'i container icinden `http://host.docker.internal:11434` olarak kullanilir.

Ollama'yi container olarak calistirmak icin:

```bash
docker compose -f compose.yml -f compose.ollama.yml up --build
docker compose -f compose.yml -f compose.ollama.yml exec ollama ollama pull qwen2.5-coder:7b
docker compose -f compose.yml -f compose.ollama.yml exec ollama ollama pull qwen3-vl:4b
```

## Smoke Kontrolleri

```bash
curl http://localhost:8000/
curl http://localhost:8001/health
curl http://localhost:8002/healthz
curl -H "X-Internal-Api-Key: dev-only-internal-api-key-change-me-0123456789abcdef" http://localhost:8003/healthz
```

`doc-ai` health endpoint'i Ollama'ya ve modele baktigi icin model pull edilmediyse `503` donebilir.

Frontend:

```text
http://localhost:5173
```

## Log ve Bakim

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mysql
docker compose run --rm backend-init
docker compose run --rm ai-views
```

DB'yi tamamen sifirlamak:

```bash
docker compose down -v
docker compose up --build
```

## Env Notlari

Tracked dev varsayilanlari `infra/env/dev.env` icindedir. Kisisel secret veya override dosyalari icin `infra/env/*.local` veya `infra/env/*.secret` kullanin; bu dosyalar git'e alinmaz.

Compose ortaminda feature flag'ler gelistirme kolayligi icin aciktir:

- `FEATURE_URETIM_PALET_PILOT_DEPO_IDS=TUMU`
- `FEATURE_AGV_DISPATCH_DEPO_IDS=TUMU`
- `FEATURE_DOC_AI_PILOT_DEPO_IDS=TUMU`
- `VITE_FEATURE_AGV_ENABLED=true`
- `VITE_FEATURE_DOC_AI_ENABLED=true`
- `VITE_FEATURE_URETIM_PALET_ENABLED=true`

## Troubleshooting

- Port cakismasi varsa `3307`, `8000`, `8001`, `8002`, `8003` veya `5173` portlarini kullanan sureci kapatin ya da compose port mapping'ini degistirin.
- `backend-init` migration hatasi verirse once `docker compose logs backend-init` ile DB baglanti ve Alembic hatasini kontrol edin.
- `ai-views` hata verirse `backend-init` tamamlanmadan view olusturulmaya calisilmadigindan ve `depo_ai_reader` kullanicisinin bootstrap ile olustugundan emin olun.
- Windows bind mount degisiklikleri gec algilanirsa polling env'leri zaten acik gelir: `WATCHFILES_FORCE_POLLING=true`, `CHOKIDAR_USEPOLLING=true`.

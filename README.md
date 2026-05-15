# Depo Yönetim Sistemi (WMS)

Lot ve palet takibi, putaway/pick görev akışları, üretim paleti kabulü, mobil terminal PWA, AGV/AMR simülasyonu, belge AI, Excel AI, sentetik veri üretimi ve operatör performansı (LMS) modülünü bir araya getiren full-stack depo yönetim sistemi.

Proje tek repoda çalışan bir geliştirme stack'i sunar: **FastAPI** ana backend, **React 19 + Vite 7** frontend, **MySQL 8.4**, **RabbitMQ**, **WmsAiService**, **DocAiService**, **ExcelAiService**, **AgvSimService** ve **DataGenService**. Yerel geliştirme için önerilen giriş noktası `compose.yml` içindeki **Docker Compose** stack'idir.

## İçindekiler

- [Öne Çıkan Özellikler](#öne-çıkan-özellikler)
- [Teknoloji Stack'i](#teknoloji-stacki)
- [Önkoşullar](#önkoşullar)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Servisler ve Portlar](#servisler-ve-portlar)
- [Repo Yapısı](#repo-yapısı)
- [Yapılandırma](#yapılandırma)
- [Yerel Geliştirme](#yerel-geliştirme)
- [Mimari Özet](#mimari-özet)
- [AI, RAG ve Yardımcı Servisler](#ai-rag-ve-yardımcı-servisler)
- [Test ve Kalite](#test-ve-kalite)
- [Operasyon Notları](#operasyon-notları)
- [Deployment Notları](#deployment-notları)
- [Sorun Giderme](#sorun-giderme)
- [Detaylı Dokümantasyon](#detaylı-dokümantasyon)

## Öne Çıkan Özellikler

- **Lot, palet ve stok yönetimi:** Palet, lot, koli ve aktif stok hesapları WMS backend tarafından yönetilir.
- **Putaway ve picking akışları:** Yerleştirme/toplama görevleri, durum geçişleri ve operatör aksiyonları takip edilir.
- **Üretim paleti kabulü:** Üretimden gelen paletler kabul, yerleştirme ve terminal akışlarına bağlanır.
- **Mobil terminal PWA:** Depocu odaklı terminal arayüzü, barkod/QR akışları ve offline kabiliyetleri destekler.
- **Operatör performansı (LMS):** Yerleştirme/toplama event'leri transactional outbox üzerinden vardiya KPI'larına dönüştürülür.
- **RabbitMQ event hattı:** `RABBITMQ_ENABLED=true` olduğunda relay + consumer worker akışı devreye girer.
- **WMS AI:** Doğal dil soruları read-only SQL view'larına veya RAG dokümanlarına yönlendirilir.
- **Doc AI:** İrsaliye PDF/görüntü belgelerinden taslak JSON çıkarır; veritabanına yazmaz.
- **Excel AI:** Yüklenen Excel/CSV dosyalarını pandas + LangChain agent ile doğal dilde yorumlar ve sütunları WMS hedef şemalarına eşler; veritabanına yazmaz.
- **AGV/AMR simülasyonu:** In-memory dünya, pathfinding, WebSocket snapshot/delta akışı ve 3D izleme UI'ı.
- **Sentetik veri üretimi:** DataGenService; Backend REST, RabbitMQ veya ML dosya çıktısı üzerinden deterministik test verisi üretir.
- **Talep tahmin çalışma alanı:** `ml_models/` altında ürün bazlı 7/30/90 günlük talep tahmini deneyleri ve entegrasyon sözleşmeleri tutulur.

## Teknoloji Stack'i

| Alan | Teknolojiler |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Alembic, PyMySQL, Pydantic Settings, JWT, APScheduler, slowapi |
| Veritabanı | MySQL 8.4, utf8mb4, Alembic migration |
| Frontend | React 19, Vite 7, React Router v7, TanStack Query v5, Tailwind CSS v4, Axios |
| PWA ve UI | vite-plugin-pwa, Workbox, Framer Motion, Recharts, lucide-react, react-hot-toast |
| AGV UI | Three.js, @react-three/fiber, @react-three/drei, Zustand |
| AI/RAG | LangChain, Ollama, ChromaDB, sentence-transformers, LlamaIndex ingestion |
| Belge işleme | pdfplumber, pypdfium2, Pillow, Ollama text/VLM modelleri |
| Excel işleme | pandas, openpyxl, langchain-experimental pandas DataFrame agent |
| ML deneyleri | pandas, scikit-learn, pydantic |
| Mesajlaşma | RabbitMQ 3 Management, pika |
| Sentetik veri | FastAPI, Typer, Faker, Pydantic, HTTPX, aio-pika, pyarrow |
| Test/Kalite | pytest, factory-boy, pytest-cov, ruff, pyright basic, ESLint 9 |
| Yerel çalışma | Docker Compose, Python service image, frontend dev image |

## Önkoşullar

Yerel geliştirme için en kısa yol Docker Compose kullanmaktır.

- Docker Desktop veya Docker Engine + Docker Compose v2
- Git
- AI özelliklerini kullanacaksanız Ollama
- Manuel çalıştırma için Python 3.x, Node.js/npm ve MySQL

**Önemli path kuralı:** Proje klasör yolu ASCII olmalıdır. Önerilen örnek:

```text
D:\Ensar Dosya\DepoUygulamasi
```

Türkçe karakterli veya bozuk encode edilmiş klasör yolları watcher, Docker bind mount, dokümantasyon ve bazı tooling akışlarında sorun çıkarabilir.

## Hızlı Başlangıç

### 1. Repoyu hazırlayın

```bash
git clone <repo-url>
cd DepoUygulamasi
```

Zaten bu klasördeyseniz doğrudan Compose adımına geçebilirsiniz.

### 2. Docker Compose stack'ini başlatın

İlk kurulumda veya dependency değişikliklerinden sonra:

```bash
docker compose up --build
```

Günlük geliştirmede arka planda başlatmak için:

```bash
docker compose up -d
```

Durumu ve backend loglarını kontrol edin:

```bash
docker compose ps
docker compose logs -f backend
```

### 3. Uygulamayı açın

| Hedef | Adres |
|---|---|
| Frontend | http://localhost:5173 |
| Backend OpenAPI | http://localhost:8000/docs |
| RabbitMQ Management | http://localhost:15672 |

RabbitMQ Management kullanıcı adı ve şifresi local stack için `guest` / `guest` değerleridir.

### 4. Stack'i durdurun

```bash
docker compose down
```

Temiz bir geliştirme veritabanı için volume'ları da kaldırın:

```bash
docker compose down -v --remove-orphans
docker compose up -d
```

### İlk çalıştırmada beklenen durumlar

- `backend-init` local seed işlemlerini çalıştırır, `alembic stamp head` uygular ve çıkar.
- `ai-views` `WmsAiService/views.sql` dosyasındaki read-only AI view'larını MySQL'e uygular ve çıkar.
- Bu iki yardımcı servisin `Exited (0)` görünmesi başarılı ve beklenen bir durumdur.

## Servisler ve Portlar

| Bileşen | Compose servisi | Adres / port | Not |
|---|---|---|---|
| Frontend | `frontend` | http://localhost:5173 | Vite dev server |
| Backend API | `backend` | http://localhost:8000 | OpenAPI: `/docs` |
| WMS AI | `wms-ai` | http://localhost:8001/health | Doğal dil, SQL, RAG |
| AGV Sim | `agv-sim` | http://localhost:8002/healthz | In-memory simülasyon |
| Doc AI | `doc-ai` | http://localhost:8003/healthz | İrsaliye çıkarımı |
| Excel AI | `excel-ai` | http://localhost:8004/healthz | Excel yorumlama + şema eşleme |
| DataGenService | `data-gen` | http://localhost:8005/healthz | Sentetik veri üretici + CLI |
| RabbitMQ AMQP | `rabbitmq` | localhost:5672 | LMS event hattı |
| RabbitMQ UI | `rabbitmq` | http://localhost:15672 | `guest` / `guest` |
| MySQL | `mysql` | localhost:3307 | Container içinde 3306 |
| LMS worker | `backend-worker` | port yok | RabbitMQ consumer |

## Repo Yapısı

```text
.
|-- BackendProje/        FastAPI ana backend, Clean Architecture, Alembic, pytest
|-- ReactProje/          React 19 + Vite 7 frontend, PWA, AGV UI
|-- WmsAiService/        Doğal dil -> SQL, doküman RAG, read-only MySQL view'ları
|-- DocAiService/        İrsaliye PDF/görüntü çıkarımı, DB'ye yazmaz
|-- ExcelAiService/      Excel/CSV yorumlama + WMS şema eşleme, DB'ye yazmaz
|-- AgvSimService/       AGV/AMR simülasyonu, WebSocket snapshot/delta
|-- DataGenService/      Sentetik WMS veri üretici servis + CLI
|-- ml_models/           Talep tahmin modeli ve ML deney alanı
|-- DOCS/agent/          Geliştirici ve AI ajan dokümantasyonu
|-- DOCS/rag/            Operatöre dönen RAG bilgi tabanı
|-- infra/               Dockerfile'lar, dev env, MySQL init dosyaları
|-- compose.yml          Yerel tam stack
|-- compose.ollama.yml   Opsiyonel container içi Ollama override'ı
|-- CLAUDE.md            AI coding agent operasyonel özeti
`-- README.md            Bu dosya
```

## Yapılandırma

### Ana env dosyası

Compose stack'i takip edilen local geliştirme dosyasını kullanır:

```text
infra/env/dev.env
```

Bu dosya sadece geliştirme kolaylığı içindir. Production veya paylaşılan gerçek ortam secret'ları için kullanılmamalıdır.

### Önemli ortam değişkenleri

| Kapsam | Değişken | Açıklama |
|---|---|---|
| Backend | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | MySQL bağlantısı |
| Backend | `JWT_SECRET_KEY` | Access/refresh token imzalama anahtarı |
| Backend/servisler | `INTERNAL_API_KEY` | Backend, Doc AI, Excel AI ve AGV arasındaki shared secret |
| Backend/LMS | `RABBITMQ_ENABLED` | `false`: DB polling aggregator, `true`: RabbitMQ relay + worker |
| Backend/LMS | `RABBITMQ_URL`, `RABBITMQ_EXCHANGE`, `RABBITMQ_QUEUE` | RabbitMQ topolojisi |
| Frontend | `VITE_BACKEND_PROXY_TARGET` | Vite `/api` proxy hedefi |
| Frontend | `VITE_FEATURE_AGV_ENABLED` | AGV izleme route/sidebar özelliği |
| Frontend | `VITE_FEATURE_DOC_AI_ENABLED` | Doc AI UI özellikleri |
| Frontend | `VITE_FEATURE_EXCEL_AI_ENABLED` | Excel AI UI özelliği (AI Asistan → Excel Analizi) |
| Backend/Excel AI | `EXCEL_AI_SERVICE_URL`, `FEATURE_EXCEL_AI_ENABLED` | Proxy hedefi ve özellik anahtarı |
| WMS AI | `OLLAMA_MODEL`, `OLLAMA_BASE_URL` | Text-to-SQL ve RAG model bağlantısı |
| WMS AI | `RAG_TOP_K`, `RAG_STRICT_DISTANCE` | RAG retrieval davranışı |
| Doc AI | `OLLAMA_TEXT_MODEL`, `OLLAMA_VLM_MODEL` | Text PDF ve VLM modeli |
| Excel AI | `OLLAMA_TEXT_MODEL`, `MAX_FILE_SIZE_MB`, `MAX_ROWS`, `MAX_SHEETS` | Pandas agent modeli ve dosya/satır limitleri |
| AGV | `WMS_BASE_URL`, `TICK_HZ`, `GRID_JSON_PATH` | Simülasyon ve WMS callback ayarları |
| DataGenService | `BACKEND_BASE_URL`, `DATAGEN_ADMIN_USERNAME`, `DATAGEN_ADMIN_PASSWORD`, `OUTPUT_DIR` | JWT login, REST/Rabbit/file hedefleri ve ML dosya çıktısı |

Tam referans için [DOCS/agent/env-reference.md](DOCS/agent/env-reference.md) dosyasını kullanın.

### Ollama

Local varsayılanlar Ollama'yı host makinede bekler:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_VLM_MODEL=qwen3-vl:4b
```

Host makinede model çekmek için:

```bash
ollama pull qwen2.5-coder:7b
ollama pull qwen3-vl:4b
```

Ollama'yı Compose içinde çalıştırmak isterseniz:

```bash
docker compose -f compose.yml -f compose.ollama.yml up -d
docker compose -f compose.yml -f compose.ollama.yml exec ollama ollama pull qwen2.5-coder:7b
docker compose -f compose.yml -f compose.ollama.yml exec ollama ollama pull qwen3-vl:4b
```

Disk notu: Varsayilan local gelistirme akisi host Ollama kullanir (`docker compose up -d --build`).
`compose.ollama.yml` sadece bilincli secildiginde eklenmelidir; bu override ile cekilen modeller
Docker volume icinde tutulur ve Docker VHDX boyutunu hizla buyutebilir.

## Yerel Geliştirme

Compose açıkken aynı servisleri aynı portlarda ayrıca `uvicorn` veya `npm run dev` ile başlatmayın. Port çakışması yaşarsınız.

### Backend

```bash
cd BackendProje
pip install -r requirements.txt
pip install -r requirements-test.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Veritabanı hazırlığı:

```bash
cd BackendProje
alembic upgrade head
python seed.py
```

### Frontend

```bash
cd ReactProje
npm install
npm run dev
```

Production build kontrolü:

```bash
cd ReactProje
npm run build
npm run preview
```

### WmsAiService

```bash
cd WmsAiService
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

Read-only view'ları ilk kez uygulamak için:

```bash
mysql -u root -p depo_yonetim < views.sql
```

### DocAiService

```bash
cd DocAiService
pip install -r requirements.txt
pip install -r requirements-test.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8003
```

Health check:

```bash
curl -H "X-Internal-Api-Key: <key>" http://127.0.0.1:8003/healthz
```

### AgvSimService

```bash
cd AgvSimService
pip install -r requirements.txt
pip install -r requirements-test.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8002
```

### ExcelAiService

```bash
cd ExcelAiService
pip install -r requirements.txt
pip install -r requirements-test.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8004
```

Health check:

```bash
curl -H "X-Internal-Api-Key: <key>" http://127.0.0.1:8004/healthz
```

### DataGenService

```bash
cd DataGenService
pip install -r requirements.txt
pip install -r requirements-test.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8005
python -m datagen run timeseries_history --count 10 --target file
```

Health check:

```bash
curl http://127.0.0.1:8005/healthz
```

## Mimari Özet

### Backend katmanları

```text
api routers -> application use cases -> core entities/repositories/services
                                      ^
                                      |
                     infrastructure persistence/DI/scheduler/services
```

- `api`: HTTP concern'leri, auth guard, request/response ve router kayıtları.
- `application`: use case orchestration, DTO ve yardımcı akışlar.
- `core`: entity, repository arayüzleri, domain service ve exception'lar.
- `infrastructure`: SQLAlchemy repository implementasyonları, DI modülleri, scheduler ve dış servis adaptörleri.

Katman kuralı içten dışa ilerler. İç katmanlar dış katmanlardan import almamalıdır.

### Backend ana dosya yapısı

```text
BackendProje/
|-- main.py
|-- database.py
|-- models.py
|-- schemas.py
|-- seed.py
|-- alembic/
|-- app/
|   |-- core/
|   |-- application/
|   |-- infrastructure/
|   `-- api/v1/routers/
`-- tests/
```

### Frontend yapısı

- `App.jsx`: React Router v7 route ağacı.
- `PrivateRoute` ve `RoleRoute`: auth ve rol koruması.
- `DashboardLayout`: admin/lojistik ve ortak korumalı ekranlar.
- `DepocuLayout`: depocu ekranları.
- `TerminalLayout`: mobil terminal ekranları.
- `queries/`: TanStack Query hook'ları ve `queryKeys.js` pattern'i.
- `services/`: Axios API istemcisi ve domain endpoint dosyaları.
- `pwa/` ve `public/`: manifest, ikonlar ve service worker akışı.

Frontend tarafında TypeScript kullanılmaz. Yeni dosyalar `.js` veya `.jsx` olarak kalmalıdır.

### Yetki rolleri

| Rol | Özet |
|---|---|
| `admin` | Yönetim, raporlama, depo ve terminal rotalarının çoğu |
| `depocu` | Terminal, stok hareketleri, üretim kabul ve kendi performansı |
| `lojistik` | Depo, kroki, stok hareketleri ve operasyonel ekranlar |
| `goruntuleyen` | Salt okunur erişim |
| `depo_ai_reader` | WmsAiService için read-only MySQL kullanıcısı |

### LMS event akışı

```text
yerlestirme/toplama use case
  -> DbOutboxPerformansEventPublisher
  -> gorev_performans_eventleri
  -> APScheduler aggregator veya RabbitMQ relay
  -> operator_vardiya_metrikleri
```

Varsayılan local mod `RABBITMQ_ENABLED=false` değeridir. Bu modda APScheduler her 5 dakikada DB polling aggregator çalıştırır. `true` olduğunda backend relay job'ı ve `backend-worker` consumer akışı kullanılır.

## AI, RAG ve Yardımcı Servisler

### WmsAiService

WmsAiService doğal dil sorularını iki ana yola yönlendirir:

- Text-to-SQL: Sadece `SELECT`, whitelist edilmiş `ai_*_view` view'ları ve read-only DB kullanıcısı.
- Doküman RAG: Operatöre dönük bilgi tabanı.

Birleşik chat endpoint'i `POST /api/ai/chat` akışında slash command, semantic router, SQL ve RAG branch'lerini birleştirir. `/sql <soru>` SQL yolunu, `/docs <soru>` doküman RAG yolunu zorlar.

### RAG korpusu

Operatöre dönen RAG bilgi tabanı yalnızca şu klasörden beslenir:

```text
DOCS/rag/**/*.md
```

`DOCS/agent/`, kök README ve geliştirici dokümanları RAG korpusuna dahil edilmez.

RAG dokümanı ekledikten veya değiştirdikten sonra:

```bash
cd WmsAiService
python ingest_docs.py --docs
pytest tests/test_rag_retrieval_quality.py -v -s
```

Router örnekleri de yenilenecekse:

```bash
cd WmsAiService
python ingest_docs.py --all
```

### DocAiService

DocAiService text PDF veya görüntü tabanlı irsaliyelerden taslak JSON çıkarır. DB'ye yazmaz; taslak kayıt, inceleme, onay/red ve WMS etkileri `BackendProje` içinde authoritative kalır.

Tüm non-OPTIONS isteklerde `X-Internal-Api-Key` zorunludur. Key eksik, yanlış veya yapılandırılmamışsa servis bilinçli olarak `503` dönebilir.

### ExcelAiService

ExcelAiService yüklenen Excel/CSV dosyasını pandas DataFrame'e çevirir ve iki akış sunar: doğal dilde soru-cevap + deterministik özet (LangChain `create_pandas_dataframe_agent` + Ollama), ve sütunların WMS hedef şemalarına (`siparis_kalemleri`, `stok_sayim_kalemleri`, `urun`) deterministik eşleme önerisi. DB'ye yazmaz; öneriler `BackendProje` tarafında değerlendirilir.

Tüm non-OPTIONS isteklerde `X-Internal-Api-Key` zorunludur. Backend proxy `FEATURE_EXCEL_AI_ENABLED=true` ile aktiflesir; flag kapalıyken `/api/excel-ai/*` 404 döner.

Detaylı plan ve mimari kararlar: [DOCS/EXCEL_AI_SERVICE_ENTEGRASYON_PLANI.md](DOCS/EXCEL_AI_SERVICE_ENTEGRASYON_PLANI.md).

### AgvSimService

AgvSimService tek süreç çalışan in-memory bir simülasyon servisidir. Replica veya multiple worker kullanılmamalıdır. Backend görevleri HTTP push ile gönderir; AGV servis tamamlanma bilgisini backend callback endpoint'lerine döner. Frontend canlı izleme için `/ws/agv` WebSocket akışını kullanır.

### DataGenService

DataGenService WMS testleri, yük denemeleri ve talep tahmin modeli eğitim verisi için sentetik veri üretir. DB'ye doğrudan yazmaz; REST hedeflerinde Backend'e JWT ile login olur, RabbitMQ hedefinde `depo.events` exchange'ine yayın yapar, file hedefinde `ml_models/talep_tahmin/data/raw/` altına parquet/CSV üretir.

Ana senaryolar: `seed_baseline`, `task_load`, `timeseries_history`, `agv_traffic`. AGV trafik senaryosu yalnız Backend yerleştirme uçlarına çağrı yapar; AgvSimService'e doğrudan istek atmaz.

Runbook: [DOCS/agent/data-gen-service.md](DOCS/agent/data-gen-service.md).

### ml_models

`ml_models/` klasörü backend akışını bozmadan ML denemeleri yapmak için ayrılmıştır. Şu an ana çalışma alanı `ml_models/talep_tahmin/` dizinidir. Hedef, ürün bazlı günlük talep serilerinden 7/30/90 günlük tahmin, stok riski, önerilen ikmal miktarı, veri yeterliliği ve güven skoru üretebilen bağımsız bir altyapı hazırlamaktır.

Bu alan FastAPI backend'i doğrudan değiştirmez. Üretime alınacak mantık net input/output sözleşmesiyle backend tarafına ayrı servis veya use case olarak taşınmalıdır.

## Test ve Kalite

| Alan | Komut | Not |
|---|---|---|
| Backend lint | `cd BackendProje && ruff check .` | Backend değişikliği sonrası önerilir |
| Backend type check | `cd BackendProje && pyright` | Basic mode, `app/` kapsamı |
| Backend test | `cd BackendProje && pytest` | Test DB: `depo_db_test` |
| Backend unit | `cd BackendProje && pytest -m unit` | Hızlı geri bildirim |
| Backend integration | `cd BackendProje && pytest -m integration` | DB gerekir |
| RabbitMQ testleri | `cd BackendProje && pytest -m rabbitmq` | Broker bilinçli açılmalı |
| Frontend lint | `cd ReactProje && npm run lint` | ESLint 9 flat config |
| Frontend build | `cd ReactProje && npm run build` | Production build kontrolü |
| Dockerfile lint | `powershell -ExecutionPolicy Bypass -File scripts/lint-docker.ps1` | Hadolint warning'leri raporlar; sadece error seviyesi komutu basarisiz yapar |
| Doc AI test | `cd DocAiService && pytest` | Extraction ve confidence testleri |
| Excel AI test | `cd ExcelAiService && pytest` | Loader, sema matcher, idempotency, router (Ollama mocked) |
| AGV test | `cd AgvSimService && pytest` | DB gerekmez |
| DataGenService test | `cd DataGenService && pytest -m unit` | Factory, emitter, API ve CLI testleri |
| RAG kalite | `cd WmsAiService && pytest tests/test_rag_retrieval_quality.py -v -s` | Doküman değişikliği sonrası |

Backend testlerinde test veritabanı adı `depo_db_test` olmalıdır. Güvenlik kontrolü `test` içermeyen DB adlarında hata verir.

## Operasyon Notları

### Migration

- Resmi migration aracı Alembic'tir.
- `BackendProje/models.py` değiştiyse migration gerekir.
- Migration oluşturmak tek başına yeterli değildir; her ortamda `alembic upgrade head` çalıştırılmalıdır.
- `main.py` lifespan akışında migration drift kontrolü vardır.
- Production'da `DEPO_STRICT_MIGRATION=1` ile drift halinde boot durdurulabilir.
- `DEPO_SKIP_MIGRATION_CHECK=1` sadece acil durum atlama için düşünülmelidir.

```bash
cd BackendProje
alembic revision --autogenerate -m "migration_aciklamasi"
alembic upgrade head
```

### RabbitMQ modu

`infra/env/dev.env` veya ilgili servis env dosyasında:

```text
RABBITMQ_ENABLED=false
```

Bu varsayılan mod eski DB polling aggregator akışıdır. RabbitMQ akışını açmak için:

```text
RABBITMQ_ENABLED=true
```

Sonra servisleri recreate edin:

```bash
docker compose up -d backend backend-worker
```

Queue ve exchange incelemek için:

```bash
docker compose exec rabbitmq rabbitmqctl list_queues name messages durable
docker compose exec rabbitmq rabbitmqctl list_exchanges name type durable
docker compose exec rabbitmq rabbitmqctl list_bindings source_name routing_key destination_name
```

Detaylı runbook: [DOCS/agent/rabbitmq-operations.md](DOCS/agent/rabbitmq-operations.md).

### AGV

- `AgvSimService` tek süreç çalışmalıdır.
- `World` in-memory singleton'dır.
- Servis restart edildiğinde state belleği sıfırlanır.
- Vite proxy'de `/ws/agv` tanımı `/api` proxy'sinden önce durmalıdır.
- Yüksek frekans AGV verisi React state'e yazılmamalıdır; UI `useFrame` içinde store'dan okunur.

### Doc AI

- `INTERNAL_API_KEY`, `X-Internal-Api-Key` ve `Idempotency-Key` sözleşmesi korunmalıdır.
- Yeni irsaliye alanı eklendiğinde prompt, entity, fixture testleri ve confidence calculator birlikte güncellenmelidir.
- DocAiService DB'ye doğrudan yazmaz.

## Deployment Notları

Bu repoda production'a özel tek bir hedef platform konfigürasyonu yoktur. Yerel geliştirme Docker Compose ile tanımlıdır; production için Docker image'larını CI/CD içinde üretip seçilen platforma göre dağıtmak en güvenli başlangıçtır.

Production'a çıkmadan önce özellikle şunları netleştirin:

- `infra/env/dev.env` içindeki dev secret'ları production'da kullanmayın.
- MySQL için managed veya yedekli bir veritabanı planı kullanın.
- RabbitMQ için `guest/guest` yerine servis bazlı kullanıcı, TLS ve monitoring planlayın.
- Deployment adımında `alembic upgrade head` çalıştırın. Local `backend-init` içindeki `alembic stamp head` production migration yerine geçmez.
- `DEPO_STRICT_MIGRATION=1` kullanmayı değerlendirin.
- `INTERNAL_API_KEY`, JWT secret ve DB parolalarını secret manager üzerinden verin.
- Frontend build çıktısını production web sunum stratejinize göre yayınlayın.
- Queue depth, DLQ, consumer lag, backend hata oranı ve MySQL yedeklerini izleyin.
- Ollama veya model servisleri production'da ayrı kaynak, timeout ve kapasite planı gerektirir.

Genel Docker build örneği:

```bash
docker build -f infra/docker/python-service.Dockerfile --build-arg SERVICE_DIR=BackendProje -t depo-backend .
docker build -f infra/docker/frontend-dev.Dockerfile -t depo-frontend-dev .
```

## Sorun Giderme

### Port çakışması

**Belirti:** `address already in use`, Vite veya Uvicorn başlamıyor.

**Çözüm:** Compose çalışıyorsa aynı servisi manuel başlatmayın.

```bash
docker compose ps
docker compose down
```

### `backend-init` veya `ai-views` exited görünüyor

**Belirti:** Yardımcı servisler `Exited (0)` durumunda.

**Çözüm:** Bu normaldir. `backend-init` seed/stamp işlemini, `ai-views` SQL view uygulamasını bitirip çıkar.

### Backend MySQL'e bağlanamıyor

**Kontrol edin:**

```bash
docker compose ps mysql
docker compose logs -f mysql
```

Host makineden MySQL portu `3307`, container içinden `3306` değeridir.

### Migration drift

**Belirti:** Startup loglarında migration drift uyarısı veya production'da boot durması.

**Çözüm:**

```bash
cd BackendProje
alembic upgrade head
```

### RabbitMQ event'leri işlenmiyor

**Kontrol edin:**

```bash
docker compose ps rabbitmq backend-worker
docker compose logs -f backend-worker
docker compose exec rabbitmq rabbitmqctl list_queues name messages
```

`RABBITMQ_ENABLED=false` ise worker ayakta olsa bile boş döngüde bekleyebilir; bu beklenen davranıştır.

### DocAiService `503` dönüyor

**Olası nedenler:**

- `INTERNAL_API_KEY` yapılandırılmamış.
- `X-Internal-Api-Key` header'ı eksik veya yanlış.
- Ollama modeli veya endpoint'i erişilemiyor.

### Excel AI menüde görünmüyor veya 404 dönüyor

**Kontrol edin:**

- Frontend için `VITE_FEATURE_EXCEL_AI_ENABLED=true` ve frontend yeniden başlatıldı mı.
- Backend için `FEATURE_EXCEL_AI_ENABLED=true` (`infra/env/dev.env`) ve backend recreate edildi mi.
- `docker compose ps excel-ai` ile servis ayakta ve `curl -H "X-Internal-Api-Key: <key>" http://localhost:8004/healthz` 200 dönüyor mu.
- Excel AI agent için Ollama'da `qwen2.5-coder:7b` modeli mevcut mu (`ollama list`).

### DataGenService senaryosu çalışmıyor

**Kontrol edin:**

- `docker compose ps data-gen backend rabbitmq` ile servisler ayakta mı.
- REST senaryoları için dev admin kullanıcısı mevcut mu (`admin/admin123`, `backend-init` logları).
- İzinsiz target kullanıldıysa API `422`, CLI exit code `2` döner; target matrisi için [DOCS/agent/data-gen-service.md](DOCS/agent/data-gen-service.md).
- Dosya çıktısı bekleniyorsa JSON `output_path` alanını ve `ml_models/talep_tahmin/data/raw/` klasörünü kontrol edin.

### WMS AI cevap vermiyor veya model timeout alıyor

**Kontrol edin:**

```bash
ollama list
ollama pull qwen2.5-coder:7b
docker compose logs -f wms-ai
```

Container içinden host Ollama'ya erişim için `OLLAMA_BASE_URL=http://host.docker.internal:11434` kullanılır.

### RAG cevabı güncel değil

Doküman değişikliklerinden sonra index'i yenileyin:

```bash
cd WmsAiService
python ingest_docs.py --docs
pytest tests/test_rag_retrieval_quality.py -v -s
```

### AGV izleme ekranı görünmüyor

`VITE_FEATURE_AGV_ENABLED=true` değerini ve frontend'in yeniden başlatıldığını kontrol edin.

```bash
docker compose up -d frontend
```

## Detaylı Dokümantasyon

| Dosya | Konu |
|---|---|
| [CLAUDE.md](CLAUDE.md) | AI coding agent operasyonel özeti ve çalışma kuralları |
| [DOCS/agent/project-architecture.md](DOCS/agent/project-architecture.md) | Mimari, roller, LMS, isimlendirme ve tech stack |
| [DOCS/agent/docker-compose.md](DOCS/agent/docker-compose.md) | Compose komutları, sağlık URL'leri, Vite/proxy ve gotcha'lar |
| [DOCS/agent/backend-notes.md](DOCS/agent/backend-notes.md) | Backend komutları, migration, test ve Clean Architecture kuralları |
| [DOCS/agent/frontend-notes.md](DOCS/agent/frontend-notes.md) | Frontend kuralları, PWA, Vite ve AGV UI notları |
| [DOCS/agent/ai-services.md](DOCS/agent/ai-services.md) | WmsAiService, DocAiService, ExcelAiService, AgvSimService ve RAG süreçleri |
| [DOCS/agent/data-gen-service.md](DOCS/agent/data-gen-service.md) | DataGenService senaryo katalogu, target matrisi, compose ve sorun giderme |
| [DOCS/EXCEL_AI_SERVICE_ENTEGRASYON_PLANI.md](DOCS/EXCEL_AI_SERVICE_ENTEGRASYON_PLANI.md) | ExcelAiService entegrasyon planı ve mimari kararlar |
| [DOCS/agent/env-reference.md](DOCS/agent/env-reference.md) | Tüm servis ortam değişkenleri |
| [DOCS/agent/rabbitmq-operations.md](DOCS/agent/rabbitmq-operations.md) | RabbitMQ event hattı, DLQ ve rollback runbook'u |

## Alt Proje README'leri

- [ReactProje/README.md](ReactProje/README.md)
- [DocAiService/README.md](DocAiService/README.md)
- [ExcelAiService/README.md](ExcelAiService/README.md)
- [AgvSimService/README.md](AgvSimService/README.md)
- [DataGenService/README.md](DataGenService/README.md)
- [ml_models/README.md](ml_models/README.md)
- [ml_models/talep_tahmin/README.md](ml_models/talep_tahmin/README.md)

## Katkı ve Geliştirme Kuralları

- Backend değişikliğinden önce ilgili router, use case, repository, entity ve test dosyalarını okuyun.
- Router -> use case -> repository zincirini tercih edin.
- Yeni DI factory'lerini `BackendProje/app/infrastructure/di/modules/` altında ekleyin ve `container.py` üzerinden re-export edin.
- ORM modeli değiştiyse Alembic migration oluşturun ve `alembic upgrade head` ile uygulayın.
- Yerleştirme/toplama görev geçişlerinde LMS `IPerformansEventPublisher` hook'unu çağırmayı unutmayın.
- Frontend'de TypeScript eklemeyin; `.js` / `.jsx` yapısına bağlı kalın.
- React Query için mevcut `queryKeys.js` pattern'ini kullanın.
- `DOCS/rag/` altında doküman değiştiyse RAG ingestion ve retrieval kalite testini çalıştırın.

# AGV / AMR Simülasyon Modülü — Mimari ve Uygulama Planı

> **Amaç:** Depo içi palet taşıma süreçlerini (yerleştirme/toplama) otonom mobil robot (AGV/AMR) simülasyonu ile canlı görselleştirmek.
> **Hedef:** Kişisel gelişim + sistem mimarisi deneyimi. Gerçek fiziksel robot yok.
> **Kapsam:** MVP — 2-5 robot, grid tabanlı depo, A*/Dijkstra pathfinding, WebSocket canlı koordinat yayını, WMS görev entegrasyonu.

---

## 1. Mevcut Sistem Analizi

### 1.1 Repo Yapısı (üst seviye)

```
DepoUygulamasi/
├── BackendProje/      # FastAPI + Clean Arch (4 katman) — WMS authoritative
├── ReactProje/        # React 19 + Vite 7 — tek SPA, üç layout (Dashboard/Depocu/Terminal)
├── WmsAiService/      # Sibling FastAPI servisi (LangChain + Ollama)
└── ml_models/         # Talep tahmin modelleri
```

### 1.2 Backend (BackendProje) — Önemli Tespitler

- **Clean Architecture** disiplini sıkı: `core → application → infrastructure → api`
- **DI modül deseni:** her domain için `app/infrastructure/di/modules/<domain>_di.py` → `container.py` re-export
- **Görev state machine'leri** zaten mevcut:
  - `YerlestirmeGorevi` (`app/core/entities/yerlestirme_gorevi.py`) — `Bekliyor → Atandi → DevamEdiyor → Tamamlandi`
  - `ToplamaGorevi` (`app/core/entities/toplama_gorevi.py`) — benzer akış
  - Atanan aktör `atanan_kullanici_id` (insan operatör). Robot, **insan operatörle aynı slottan görev çekecek** ya da yeni bir aktör tipi tanımlanacak.
- **Event publisher pattern** mevcut: `IPerformansEventPublisher` + outbox tablosu. AGV için benzer bir hook noktası kullanılabilir (zorunlu değil, MVP'de basit HTTP yeterli).
- **Async altyapı:** APScheduler `app/infrastructure/scheduler/` altında periyodik joblar çalıştırıyor; FastAPI lifespan ile başlıyor. Tick loop için bu altyapı **referans alınabilir ama AGV içinde ayrı `asyncio.create_task` döngüsü tercih edilmeli** (AGV servisi ayrı süreç).
- **Auth:** JWT + role; `depocu/admin/lojistik`. Robot için service-to-service için **shared secret HMAC veya basit `INTERNAL_API_KEY` header** yeterli (MVP).

### 1.3 Frontend (ReactProje) — Önemli Tespitler

- TypeScript YOK; tüm dosyalar `.js` / `.jsx`
- Routing: `App.jsx` → `react-router-dom` v7, `PrivateRoute` + `RoleRoute`
- Data fetching: TanStack React Query, `queryKeys.js` + domain bazlı `queries/*Queries.js`
- HTTP: tek `services/api.js` Axios instance (Bearer auto-inject + 401 refresh)
- Üç layout: `DashboardLayout`, `DepocuLayout`, `TerminalLayout`
- `DepoKrokiPage.jsx` zaten 2D depo görselleştirmesi yapıyor → AGV sayfası **bunun 3D evrimi** olarak konumlandırılabilir

### 1.4 WmsAiService — Referans Olarak

- Sibling süreç (port 8001) FastAPI, `BackendProje` (port 8000) ile HTTP üzerinden konuşuyor
- DB'ye **read-only** kullanıcıyla bağlanıyor (`depo_ai_reader`)
- AGV servisi de aynı sibling deseni ile kurulacak; **DB erişimi ya yok ya da çok sınırlı read-only**

### 1.5 Mevcut Sistemden Yararlanılacak Yerler

| Kaynak | Kullanım |
|---|---|
| `Raf` entity (`koridor`, `kat`, `goz`) | Grid haritasının seed verisi |
| `Depo` entity | AGV'nin çalıştığı depo bağlamı |
| `YerlestirmeGorevi` / `ToplamaGorevi` | AGV'nin tamamlayacağı WMS görevleri |
| `Palet` entity | Robotun taşıdığı yük |
| `IPerformansEventPublisher` deseni | AGV görev tamamlama event'i için referans |
| APScheduler/lifespan | Tick loop hayat döngüsü için referans |

---

## 2. Önerilen Hibrit Mimari

```
┌──────────────────────────┐         ┌──────────────────────────┐
│  BackendProje (8000)     │  HTTP   │  AgvSimService (8002)    │
│  WMS authoritative       │────────▶│  Robot simülasyon motoru │
│  - YerlestirmeGorevi     │ (görev  │  - Tick loop (asyncio)   │
│  - ToplamaGorevi         │  push)  │  - Pathfinding (A*)      │
│  - Palet / Raf / Depo    │         │  - Robot state           │
│                          │◀────────│  - In-memory dünya       │
│                          │ (görev   │                          │
│                          │  done)   │                          │
└──────────────────────────┘         └────────────┬─────────────┘
            ▲                                     │ WebSocket
            │ REST (TanStack Query)               │ /ws/agv (telemetry @ 5–10 Hz)
            │                                     ▼
┌──────────────────────────────────────────────────────────────┐
│  ReactProje (5173)                                           │
│  - /agv-izleme route (DashboardLayout altında)               │
│  - WS client (zustand store, React state DIŞINDA)            │
│  - Three.js sahne (@react-three/fiber + drei)                │
│  - Görev paneli WMS verilerini React Query ile alır          │
└──────────────────────────────────────────────────────────────┘
```

**Önemli sınırlar:**

- **WMS source-of-truth** `BackendProje`'dir. AGV servisi WMS state'i **kopyalamaz**, sadece *çalışırken gerekli olan in-flight bilgiyi* (atanmış görevler, robot konumları) bellekte tutar.
- **AGV servisi DB yazmaz.** Görev tamamlanınca `BackendProje`'nin var olan tamamlama endpoint'ini çağırır.
- **Frontend business logic barındırmaz.** Pathfinding, görev atama, durum geçişi backend'de. Frontend sadece koordinatları render eder.
- **Tick frekansı server-side (5-10 Hz).** Frontend interpolasyonla 60 FPS render eder ama otoriter konum servertedir.

---

## 3. Yeni Klasör Yapıları

### 3.1 Backend — `AgvSimService/`

```
AgvSimService/
├── main.py                          # FastAPI app, lifespan'de tick loop başlat
├── config.py                        # Settings (pydantic-settings) — DB yok, sadece WMS_BASE_URL, INTERNAL_API_KEY, TICK_HZ
├── requirements.txt
├── .env.example
├── app/
│   ├── core/                        # Saf simülasyon domain'i (DB/HTTP yok)
│   │   ├── entities/
│   │   │   ├── robot.py             # Robot entity + state machine
│   │   │   ├── grid.py              # Grid (cell types: bos, raf, koridor, sarj, engel)
│   │   │   ├── path.py              # Path value object (cell listesi)
│   │   │   └── agv_gorev.py         # AGV görev (WMS görev id'sine referans)
│   │   ├── services/
│   │   │   ├── pathfinding.py       # A* (4-yönlü, manhattan heuristic)
│   │   │   ├── world.py             # Dünya state'i (robotlar + grid + görev kuyruğu)
│   │   │   └── collision.py         # Reservation table (basit zaman-uzay rezervasyonu)
│   │   └── exceptions.py
│   ├── application/
│   │   ├── use_cases/
│   │   │   ├── gorev_atama.py       # WMS'ten gelen görevi uygun robota ata
│   │   │   ├── tick.py              # Bir tick'i ilerlet (tüm robotları)
│   │   │   ├── gorev_kabul.py       # Robot yeni göreve başlasın
│   │   │   └── gorev_tamamla.py     # WMS'e callback gönder
│   │   └── dto/
│   │       ├── telemetri_dto.py     # WS yayını payload'ı
│   │       ├── gorev_dto.py         # Inbound (WMS → AGV) ve outbound (AGV → WMS)
│   │       └── robot_dto.py
│   ├── infrastructure/
│   │   ├── wms_client.py            # httpx async client → BackendProje
│   │   ├── grid_loader.py           # Depo+raf'lardan grid üret (BackendProje API'ından çek)
│   │   └── ws_broadcaster.py        # WebSocket connection manager + broadcast
│   ├── api/
│   │   └── v1/
│   │       ├── routers/
│   │       │   ├── gorevler.py      # POST /api/agv/gorevler (WMS push)
│   │       │   ├── robotlar.py      # GET /api/agv/robotlar (snapshot)
│   │       │   └── ws.py            # WS /ws/agv (telemetry stream)
│   │       └── auth.py              # INTERNAL_API_KEY + (opsiyonel) JWT passthrough
│   └── runtime/
│       └── tick_loop.py             # asyncio.create_task — saniyede TICK_HZ kez tick
└── tests/
    ├── unit/
    │   ├── test_pathfinding.py
    │   ├── test_robot_state.py
    │   └── test_grid.py
    └── integration/
        └── test_gorev_lifecycle.py
```

### 3.2 Backend — `BackendProje/` Tarafında Eklenecekler

> **Yeni domain DEĞİL**, mevcut domain'lere ince hook'lar:

```
BackendProje/app/
├── core/services/
│   └── agv_dispatcher.py            # (yeni) AGV'ye görev göndermeye karar verir (feature flag)
├── infrastructure/services/
│   └── agv_sim_client.py            # (yeni) httpx ile AgvSimService çağırır
├── api/v1/routers/
│   └── agv_callbacks.py             # (yeni) AGV'den gelen "görev tamamlandı/başladı" callback'leri
└── infrastructure/di/modules/
    └── agv_di.py                    # (yeni) factory'ler
```

**Feature flag:** `FEATURE_AGV_DISPATCH_DEPO_IDS` (boş=kapalı, `1,3`=belirli depolar). Mevcut `FEATURE_URETIM_PALET_PILOT_DEPO_IDS` ile aynı desen.

### 3.3 Frontend — `ReactProje/` Tarafında Eklenecekler

```
ReactProje/src/
├── pages/
│   └── agv/
│       ├── AgvIzlemePage.jsx        # /agv-izleme — ana sayfa
│       └── components/
│           ├── DepoSahnesi.jsx      # <Canvas> — sahnenin kökü
│           ├── DepoZemini.jsx       # Grid + raflar (instanced mesh)
│           ├── Robot.jsx            # Tek robot mesh + interpolasyon
│           ├── RobotYollari.jsx     # Aktif rotaları gösterir
│           ├── GorevPaneli.jsx      # Sağ panel — aktif görevler tablosu (React Query)
│           └── BaglanitiDurumu.jsx  # WS bağlantı göstergesi
├── stores/
│   └── agvStore.js                  # zustand — robot konumları (yüksek frekans)
├── hooks/
│   ├── useAgvWebSocket.js           # WS bağlantı + reconnect + zustand'a yaz
│   └── useAgvInterpolation.js       # Tick verisini 60FPS'e interpole et
├── queries/
│   └── agvQueries.js                # WMS görevleri + robot listesi (React Query)
└── services/
    └── agvApi.js                    # Snapshot endpoint'leri için Axios
```

**Bundle ayrımı:** `vite.config.js`'te `agv-vendor` chunk'ı ekle (`three`, `@react-three/fiber`, `@react-three/drei`, `zustand`) → ana SPA bundle şişmesin.

---

## 4. Kullanılacak Teknolojiler

### 4.1 Backend (AgvSimService)

| Teknoloji | Sürüm | Amaç |
|---|---|---|
| Python | 3.11+ | (BackendProje ile uyumlu) |
| FastAPI | son | HTTP + WebSocket |
| uvicorn | son | ASGI server |
| pydantic-settings | son | `.env` okuma |
| httpx | son | WMS callback (async) |
| asyncio | stdlib | Tick loop, WS broadcast |
| pytest, pytest-asyncio | son | Test |

> **Kasıtlı olarak YOK:** SQLAlchemy, Alembic, Redis, Kafka, Celery, ROS2, fizik motoru. AGV servisi **stateless-from-DB** — tüm canlı state in-memory.

### 4.2 Frontend

| Paket | Amaç |
|---|---|
| `three` | WebGL primitives |
| `@react-three/fiber` | React reconciler for three |
| `@react-three/drei` | Helper'lar (OrbitControls, Stats, Instances, Text) |
| `zustand` | Yüksek frekanslı robot state (React render dışında) |

---

## 5. Backend Mimarisi (AgvSimService)

### 5.1 Katmanlama

`AgvSimService` mini-Clean Arch izler ama **çok daha hafif**:

- `core` — domain (Robot, Grid, Path) ve saf algoritmalar (A*)
- `application` — use case'ler (atama, tick, tamamla)
- `infrastructure` — WMS HTTP client, WS broadcaster
- `api` — FastAPI router'ları
- `runtime` — tick loop (lifespan tarafından yönetilir)

### 5.2 Çekirdek Bileşenler

#### 5.2.1 `World` (in-memory singleton)

```
World
├── grid: Grid                # Statik (boot'ta yüklenir)
├── robotlar: dict[id, Robot] # Anlık konum, state, atanan görev
├── gorev_kuyrugu: list[AgvGorev]  # Atanmamış görevler
├── reservation_table: dict[(x,y,t), robot_id]  # Basit çakışma önleme
└── tick_no: int
```

`World` **process-local**. Birden fazla replica DEĞİL (tek süreç).

#### 5.2.2 Robot State Machine

(Bkz. §9)

#### 5.2.3 Tick Loop

```
async def tick_loop():
    while True:
        await asyncio.sleep(1.0 / TICK_HZ)
        with world.lock:
            tick_use_case.execute(world)        # 1. Robotları 1 hücre ilerlet
            atama_use_case.try_dispatch(world)  # 2. Bekleyen görev varsa boş robota ata
            telemetri = world.snapshot()
        await ws_broadcaster.broadcast(telemetri)  # 3. Tüm bağlı client'lara yay
        # 4. Tamamlanan görevler için arka plan WMS callback (gather, fire-and-forget)
```

`TICK_HZ` env'den (default 5). Tick içi iş **CPU-light** olmalı (lock altında).

### 5.3 BackendProje Tarafındaki Hooklar

- **Görev oluşturulunca dispatch:** `YerlestirmeGoreviOlusturUseCase` sonunda (görev `Bekliyor` durumunda) `AgvDispatcher` çağrılır. Feature flag açıksa görev AGV'ye HTTP POST'lanır (fire-and-forget, hata olursa loglar ama görev WMS'te kalır — manuel operatör fallback).
- **AGV callback:** `POST /api/agv-callbacks/gorev-tamamlandi` → AGV'nin gerçek raf yerleştirmesini WMS'in mevcut `tamamla` use case'iyle yansıtır. **Robot için synthetic `Kullanici` (rol=`agv`)** kullanılır → LMS metrikleri kirlenmez (filtre eklenebilir).
- **Yetkilendirme:** Servisler arası `X-Internal-Api-Key` header. Ayrıca `BackendProje`'de bu router'a sadece bu header ile erişim.

---

## 6. Frontend Mimarisi (ReactProje)

### 6.1 Sayfa Yerleşimi

```
/agv-izleme  (DashboardLayout altında, RoleRoute: admin + lojistik)
├── Sol: <DepoSahnesi> (Three.js Canvas, ekranın %75'i)
└── Sağ: <GorevPaneli> + <RobotListesi> + <BaglanitiDurumu>
```

### 6.2 State Yönetimi — Kritik Karar

**React state'e yüksek frekanslı veri YAZMA.** Aksi halde tüm sayfa 5-10 Hz re-render eder.

```
┌─────────────────────────────────────────┐
│  WebSocket onmessage (5-10 Hz)          │
│        │                                 │
│        ▼                                 │
│  zustand store (robotlar konumları)      │
│        │                                 │
│        ▼ (React render TETIKLEMEZ —      │
│        │  doğrudan ref/store oku)        │
│        ▼                                 │
│  useFrame() hook (60 FPS, R3F içi)       │
│        │                                 │
│        ▼                                 │
│  mesh.position.lerp(hedef, factor)       │
│  → THREE objesi mutate, React render YOK │
└─────────────────────────────────────────┘
```

**Sadece şunlar React state:**
- WS bağlantı durumu (bağlı/kopuk)
- Aktif robot listesi (id'ler — sayı/değişim olunca)
- Seçili robot (kullanıcı tıkladığında)
- Görev paneli (React Query — REST'ten 5-10 sn cache)

### 6.3 Render Optimizasyonu

- **Raflar:** `<Instances>` ile tek draw call (1000 raf bile tek mesh)
- **Robotlar:** Az olduğu için ayrı mesh; `useFrame` içinde lerp
- **Yollar:** `LineSegments` veya `<Line>` (drei)
- **Kamera:** `OrbitControls` (drei)
- **Stats:** dev'de `<Stats>` (drei) — FPS göstergesi

---

## 7. WebSocket Veri Akışı

### 7.1 Endpoint

`AgvSimService` → `WS /ws/agv?depo_id=1`

- Client bağlanır → server **ilk mesajda full snapshot** gönderir
- Sonra her tick'te **delta** mesajları gönderir
- Bağlantı kopunca client exponential backoff ile yeniden bağlanır (1s → 2s → 4s → max 10s)

### 7.2 Mesaj Formatları

**Server → Client (snapshot, ilk mesaj):**
```json
{
  "tip": "snapshot",
  "tick_no": 1234,
  "ts": 1730000000.123,
  "grid": { "genislik": 50, "yukseklik": 30, "raflar": [...] },
  "robotlar": [
    { "id": "AGV-01", "x": 5.0, "y": 10.0, "yon": "K", "durum": "Bos" }
  ]
}
```

**Server → Client (delta, her tick):**
```json
{
  "tip": "delta",
  "tick_no": 1235,
  "ts": 1730000000.323,
  "robotlar": [
    { "id": "AGV-01", "x": 5.0, "y": 11.0, "yon": "K", "durum": "Tasiyor", "gorev_id": 42 }
  ]
}
```

**Server → Client (event, sıkça değişmeyen şeyler):**
```json
{ "tip": "event", "olay": "gorev_atandi", "robot_id": "AGV-01", "gorev_id": 42 }
{ "tip": "event", "olay": "gorev_tamamlandi", "robot_id": "AGV-01", "gorev_id": 42 }
{ "tip": "event", "olay": "rota_hesaplandi", "robot_id": "AGV-01", "rota": [[5,10],[5,11],...] }
```

**Client → Server:** MVP'de yok. (Faz 2: manuel duraklat/sürdür komutları)

### 7.3 Backpressure

- WS göndermeden önce `len(send_queue) > N` ise bağlantı kapatılır (yavaş client diğerlerini engellemesin)
- Tick içi broadcast `asyncio.gather(..., return_exceptions=True)` — bir client hata verirse diğerleri etkilenmesin

---

## 8. Request / Response Örnekleri

### 8.1 BackendProje → AgvSimService (görev push)

```http
POST http://localhost:8002/api/agv/gorevler
X-Internal-Api-Key: <secret>
Content-Type: application/json

{
  "wms_gorev_id": 142,
  "wms_gorev_tipi": "Yerlestirme",
  "depo_id": 1,
  "kaynak": { "tip": "raf", "raf_id": 88, "x": 2, "y": 5 },
  "hedef":  { "tip": "raf", "raf_id": 412, "x": 18, "y": 20 },
  "palet_id": 990,
  "oncelik": 5
}
```

**200 OK:**
```json
{ "kabul_edildi": true, "agv_gorev_id": "agv-7a3f", "tahmini_baslangic_tick": 1240 }
```

### 8.2 AgvSimService → BackendProje (görev tamamlama callback)

```http
POST http://localhost:8000/api/agv-callbacks/gorev-tamamlandi
X-Internal-Api-Key: <secret>
Content-Type: application/json

{
  "wms_gorev_id": 142,
  "wms_gorev_tipi": "Yerlestirme",
  "robot_id": "AGV-01",
  "gerceklesen_raf_id": 412,
  "sim_baslama_tick": 1240,
  "sim_tamamlanma_tick": 1380,
  "rota_uzunlugu": 28
}
```

### 8.3 Snapshot (REST, ilk yükleme için)

```http
GET http://localhost:8002/api/agv/robotlar?depo_id=1
```

```json
{
  "tick_no": 1234,
  "robotlar": [
    { "id": "AGV-01", "x": 5.0, "y": 10.0, "durum": "Bos", "batarya": 0.82 }
  ]
}
```

---

## 9. Robot State Machine

```
                    ┌───────────────┐
                    │     Bos       │◀────────────┐
                    │ (idle, sarj)  │             │
                    └───────┬───────┘             │
                            │ gorev_atandi        │
                            ▼                     │
                  ┌────────────────────┐          │
                  │ KaynagaGidiyor     │          │
                  │ (boş, kaynağa)     │          │
                  └─────────┬──────────┘          │
                            │ kaynaga_vardi       │
                            ▼                     │
                  ┌────────────────────┐          │
                  │ Yukluyor           │          │
                  │ (1-2 tick bekler)  │          │
                  └─────────┬──────────┘          │
                            │ palet_alindi        │
                            ▼                     │
                  ┌────────────────────┐          │
                  │ Tasiyor            │          │
                  │ (yüklü, hedefe)    │          │
                  └─────────┬──────────┘          │
                            │ hedefe_vardi        │
                            ▼                     │
                  ┌────────────────────┐          │
                  │ Birakiyor          │          │
                  │ (1-2 tick bekler)  │          │
                  └─────────┬──────────┘          │
                            │ palet_birakildi     │
                            ▼                     │
                  ┌────────────────────┐          │
                  │ TamamlandiBildirim │          │
                  │ (WMS callback)     │          │
                  └─────────┬──────────┘          │
                            │ wms_onayladi        │
                            └─────────────────────┘

   Yan akış (her durumdan):
   - HataDuruyor    (yol bulunamadı / WMS callback başarısız → manuel müdahale)
   - DusukBatarya   (Bos durumuna dönüşte tetiklenir → şarj rafına git)
```

**Tasarım notu:** State machine `app/core/entities/robot.py` içinde **WMS'in `YerlestirmeGorevi` desenini birebir taklit eder** (`_GECISLER` dict + `_durum_gecisi`). Tutarlı kod hissi için.

---

## 10. Pathfinding Yaklaşımı

### 10.1 Algoritma Seçimi — A*

**Neden A*:**
- Grid tabanlı, uniform cost (her hücre = 1)
- Manhattan distance heuristic kabul edilebilir (4-yönlü hareket)
- Open-source referans bol; debug kolay
- Dijkstra yeter aslında ama A* heuristic ile daha hızlı; kod kompleksitesi farkı yok

### 10.2 Grid Üretimi

`AgvSimService` boot'ta veya görev geldiğinde **`BackendProje`'den depo + raf bilgisini çeker** (read-only):
- `GET /api/depolar/{id}` + `GET /api/raflar?depo_id={id}`
- `Raf.koridor + Raf.kat + Raf.goz` → grid (x, y) eşlemesi
- Cell tipleri: `BOS` (geçilebilir), `RAF` (engel ama hedef olabilir), `SARJ`, `ENGEL`

> **MVP:** Grid eşlemesi *manuel bir JSON dosyasıyla* yapılabilir (`AgvSimService/data/depo_1_grid.json`). DB'den otomatik üretim Faz 2.

### 10.3 Çakışma Önleme — Basit

MVP için **Cooperative A* light**:
- Her robot rotasını hesaplarken, diğer robotların *önümüzdeki N tick* hücrelerini engel sayar
- Çakışma durumunda biri 1 tick bekler (priority = robot_id)
- Deadlock detection: 5 tick boyunca hareket etmeyen robotlar `HataDuruyor`'a geçer

> **Yapmıyoruz:** Tam multi-agent pathfinding (CBS, M*, vs.). Aşırı kompleks. MVP'de 2-5 robot için coop A* fazlasıyla yeterli.

### 10.4 Yeniden Hesaplama

- Yol kapatılırsa (yeni statik engel) → tüm robotların rotaları yeniden hesaplanır
- Robot 5 tick boyunca beklemekte ise → rotasını iptal edip yeniden hesaplar

---

## 11. Faz Bazlı Roadmap

### **Faz 0 — Hazırlık (1-2 gün)**
- Klasörler oluştur (`AgvSimService/`, frontend `pages/agv/`, `stores/`)
- `requirements.txt`, `.env.example`, `package.json` deps eklemeleri
- `vite.config.js` chunk ekle, route guard ekle

### **Faz 1 — AgvSimService MVP (3-5 gün)**
- Statik JSON grid yükle
- Robot entity + state machine
- A* pathfinding (tek robot, çakışma yok)
- Tick loop + WS broadcaster
- Görev kabul endpoint (yapay test çağrısıyla doğrula)
- Unit testler (pathfinding, state machine)

### **Faz 2 — Frontend MVP (3-5 gün)**
- `/agv-izleme` route + iskelet
- Three.js sahnesi: zemin + raflar (instanced) + robotlar
- WS bağlantı (zustand store)
- `useFrame` interpolasyonu
- OrbitControls + temel UI panel
- WS reconnect

### **Faz 3 — WMS Entegrasyonu (3-4 gün)**
- `BackendProje` tarafında `agv_dispatcher` + `agv_callbacks` router
- Feature flag `FEATURE_AGV_DISPATCH_DEPO_IDS`
- Synthetic `agv` kullanıcı seed
- Yerlestirme görevi → AGV → callback → WMS tamamlama akışı E2E
- Integration test (BackendProje + AgvSimService aynı anda çalışırken)

### **Faz 4 — Çoklu Robot + Çakışma (2-3 gün)**
- Cooperative A* light (rezervasyon tablosu)
- Deadlock tespiti + recovery
- 2-5 robot ile yük testi
- Frontend: çoklu robot rendering + tıklama → seçim

### **Faz 5 — Cilalama (2 gün)**
- Bağlantı durumu göstergesi, hata UI
- Robot batarya simülasyonu (azalır → şarja gider)
- Görev paneli (React Query — aktif görevler)
- Dev `<Stats>` + performance audit
- README ve `.env.example` dokümantasyonu

> **Toplam tahmini:** ~14-21 iş günü (kişisel proje hızında — paralel çalışılacak başka bir görev yok varsayımı).

---

## 12. Checklist Görev Listesi

### Backend — AgvSimService
- [ ] Klasör + `main.py` + `config.py` + `.env.example` oluştur
- [ ] `requirements.txt` (fastapi, uvicorn, httpx, pydantic-settings, pytest, pytest-asyncio)
- [ ] `core/entities/grid.py` — `Cell`, `Grid` (genişlik, yükseklik, cell tipleri)
- [ ] `core/entities/robot.py` — Robot + RobotDurum state machine
- [ ] `core/entities/path.py` — Path value object
- [ ] `core/entities/agv_gorev.py` — AGV görev (WMS id ref)
- [ ] `core/services/pathfinding.py` — A* implementasyonu (test'li)
- [ ] `core/services/world.py` — World singleton + lock
- [ ] `core/services/collision.py` — Reservation table + deadlock tespiti
- [ ] `application/use_cases/tick.py` — Bir tick'i ilerlet
- [ ] `application/use_cases/gorev_atama.py` — Boş robota görev ata
- [ ] `application/use_cases/gorev_tamamla.py` — WMS callback
- [ ] `application/dto/telemetri_dto.py`, `gorev_dto.py`, `robot_dto.py`
- [ ] `infrastructure/wms_client.py` — httpx async client
- [ ] `infrastructure/grid_loader.py` — JSON'dan grid yükle (Faz 1) / API'dan (Faz 2)
- [ ] `infrastructure/ws_broadcaster.py` — Connection manager
- [ ] `api/v1/routers/gorevler.py` — POST /api/agv/gorevler
- [ ] `api/v1/routers/robotlar.py` — GET snapshot
- [ ] `api/v1/routers/ws.py` — WS endpoint
- [ ] `api/v1/auth.py` — INTERNAL_API_KEY check
- [ ] `runtime/tick_loop.py` — asyncio task lifecycle
- [ ] `main.py` lifespan: tick loop + grid yükleme
- [ ] `tests/unit/test_pathfinding.py`
- [ ] `tests/unit/test_robot_state.py`
- [ ] `tests/integration/test_gorev_lifecycle.py`

### Backend — BackendProje (Hooklar)
- [ ] `app/core/services/agv_dispatcher.py` — Feature flag kontrolü + dispatch karar
- [ ] `app/infrastructure/services/agv_sim_client.py` — httpx ile AgvSimService POST
- [ ] `app/infrastructure/di/modules/agv_di.py` + `container.py` re-export
- [ ] `app/api/v1/routers/agv_callbacks.py` — POST /api/agv-callbacks/gorev-tamamlandi
- [ ] `main.py` router kayıt
- [ ] `app/core/config.py` — `FEATURE_AGV_DISPATCH_DEPO_IDS`, `AGV_SIM_SERVICE_URL`, `INTERNAL_API_KEY`
- [ ] Synthetic `agv` rolü/kullanıcısı için seed (rol enum'a eklenir mi yoksa özel mi?)
- [ ] `YerlestirmeGoreviOlusturUseCase` sonuna dispatcher hook (sadece flag açıkken)
- [ ] Mevcut testleri kırmadığını doğrula (`pytest`)

### Frontend — ReactProje
- [ ] `package.json`: `three`, `@react-three/fiber`, `@react-three/drei`, `zustand` ekle
- [ ] `vite.config.js`: `agv-vendor` chunk
- [ ] `App.jsx`: `/agv-izleme` route (admin + lojistik)
- [ ] `pages/agv/AgvIzlemePage.jsx` (iskelet)
- [ ] `pages/agv/components/DepoSahnesi.jsx` (Canvas + OrbitControls)
- [ ] `pages/agv/components/DepoZemini.jsx` (instanced raflar)
- [ ] `pages/agv/components/Robot.jsx` (mesh + useFrame interpolasyon)
- [ ] `pages/agv/components/RobotYollari.jsx`
- [ ] `pages/agv/components/GorevPaneli.jsx`
- [ ] `pages/agv/components/BaglanitiDurumu.jsx`
- [ ] `stores/agvStore.js` (zustand)
- [ ] `hooks/useAgvWebSocket.js` (reconnect + zustand yaz)
- [ ] `services/agvApi.js` (snapshot)
- [ ] `queries/agvQueries.js` + `queryKeys.js`'e ekleme
- [ ] Sidebar menüsüne "AGV İzleme" eklemesi (rol filtreli)
- [ ] `npm run lint` temiz
- [ ] `npm run build` chunk boyutu mantıklı

### Dokümantasyon
- [ ] `AgvSimService/README.md` — kurulum + çalıştırma
- [ ] `CLAUDE.md` güncellemesi (tech stack, project structure, env değişkenleri)
- [ ] `.env.example` her iki tarafta güncel

---

## 13. Riskler ve Dikkat Edilmesi Gerekenler

### 13.1 Performans Riskleri

| Risk | Nasıl Engellenir |
|---|---|
| Frontend her tick'te re-render → 5-10 Hz tüm sayfa yenilenir | zustand + useFrame; React state'ten YÜKSEK FREKANS dışında tut |
| Çok sayıda raf draw call'u şişirir | `<Instances>` ile tek mesh |
| WS payload çok büyük → ağ darboğazı | Snapshot + delta ayrımı; sadece değişen robotlar gönder |
| Tick loop CPU'yu meşgul eder, FastAPI yavaşlar | Tick içi iş minimal; sleep + asyncio.gather; CPU-bound kısımları kısa tut |
| Pathfinding O(grid) — çok robot çok hesap | Rota bulunduktan sonra cache; sadece engel değişince yeniden hesapla |

### 13.2 Mimari Riskleri

| Risk | Önlem |
|---|---|
| AGV servisi WMS state'i kopyalamaya başlar (drift) | **AGV sadece in-flight veriyi tutar**; persist YOK; restart'ta WMS'ten beklemekte olan görevleri çeker |
| WMS callback başarısız → görev yarım kalır | Robot `HataDuruyor` → operatör manuel müdahale; idempotency key (Idempotency-Key header WMS callback'inde) |
| Servisler arası secret leak | Sadece `127.0.0.1` bind; `INTERNAL_API_KEY` env'de; CORS sıkı |
| Frontend WS koparsa kullanıcı fark etmez | `BaglanitiDurumu` göstergesi + reconnect + "X saniyedir bağlı değil" uyarısı |
| Birden fazla AGV servisi instance → world tutarsızlığı | **Tek süreç zorunluluğu** (README'de açıkça belirt); MVP'de scaling yok |
| Synthetic `agv` kullanıcısı LMS metriklerini bozar | LMS aggregator'ında `rol != 'agv'` filtresi (veya `kullanici_id IS NOT NULL AND aktif=True`) |

### 13.3 Geliştirme Riskleri

| Risk | Önlem |
|---|---|
| Three.js öğrenme eğrisi büyük | Faz 2'de **drei helper'larıyla başla** (OrbitControls, Instances); özel shader yazma |
| Pathfinding bug'ları görsel debug zor | AgvSimService log: her rotayı koordinat dizisi olarak yaz; frontend "rotayı çiz" özelliği erken gelsin |
| Aynı anda iki süreç çalıştırma karmaşası | Kök dizinde `start-dev.sh` (BackendProje + AgvSimService + Vite paralel) |
| Mevcut WMS testleri kırılır | Feature flag default OFF; `agv_dispatcher` flag kapalıyken hiçbir şey yapmaz; CI'da flag kapalı kalır |

### 13.4 Yapılmaması Gerekenler (kullanıcı isteği)

- ❌ Kafka, RabbitMQ, Redis Pub/Sub
- ❌ Kubernetes, Docker Compose'tan öteye gitmek
- ❌ Distributed cluster, sharding, multi-process world
- ❌ ROS2, SLAM, gerçek fizik motoru (Bullet/Cannon)
- ❌ Mikroservis orkestrasyonu, service mesh
- ❌ TypeScript'e geçiş (frontend `.js`/`.jsx` kalır)
- ❌ Yeni veritabanı (Postgres, MongoDB, neo4j)

---

## 14. Önerilen İlk MVP Planı

> **Hedef:** 2 hafta sonunda, kullanıcının `/agv-izleme` sayfasını açıp **bir görev oluşturduğunda** (yerleştirme görevi) **3D depoda bir robotun yola çıktığını, palete gidip aldığını ve hedef rafa götürüp WMS'te görevi tamamladığını** görmesi.

### MVP Kapsamı (NET)

**İçindeki:**
- Tek depo (`depo_id=1`), elle hazırlanmış JSON grid (50×30 hücre, ~30 raf)
- 2 robot (`AGV-01`, `AGV-02`)
- A* pathfinding, basit "diğer robotun mevcut hücresini engel say" çakışma kuralı (full coop A* Faz 4)
- Yalnızca `Yerlestirme` görevi (Toplama Faz 5)
- BackendProje feature flag açıkken yeni yerleştirme görevi → AGV'ye düşer
- Frontend `/agv-izleme`: 3D sahne + canlı robotlar + sağ panelde aktif görevler tablosu
- WS reconnect, snapshot+delta protokolü
- Görev tamamlanınca WMS'te `YerlestirmeGorevi.tamamla` çağrılır (synthetic `agv` user)

**Dışındaki (sonraki fazlara):**
- Toplama görevleri
- Batarya simülasyonu
- Çoklu depo
- Otomatik grid üretimi (raf koordinatlarından)
- Manuel komutlar (frontend → AGV: dur/sürdür)
- Performans paneli (UPH benzeri)
- Üretim deployment'ı

### MVP Acceptance Kriterleri

1. Backend ayağa kalkar, `GET /healthz` döner
2. `POST /api/agv/gorevler` ile manuel görev gönderilebilir, WS'te robotun hareket ettiği görülür
3. WMS feature flag açıkken yerleştirme görevi oluşturmak AGV'ye dispatch eder, WMS'te görev `Tamamlandi` ile kapanır
4. `/agv-izleme` sayfası açıldığında 60 FPS render eder (Stats ile doğrulanır)
5. WS bağlantısı koparsa otomatik reconnect olur
6. `pytest` ve `npm run lint` temiz geçer

---

## Özet — Bir Bakışta Plan

- **Yeni servis:** `AgvSimService/` (FastAPI, port 8002, in-memory, DB yok)
- **Frontend:** `ReactProje/` içinde `/agv-izleme` sayfası, Three.js + R3F + drei + zustand
- **WMS entegrasyonu:** Feature flag'li dispatcher + callback router; mevcut görev state machine'leri korunur
- **Veri akışı:** WMS HTTP push → AGV simüle → WS broadcast (5-10 Hz) → frontend interpolate → görev bitti AGV → WMS HTTP callback
- **Yapılmıyor:** Kafka, K8s, ROS2, fizik motoru, distributed cluster
- **İlk MVP:** ~2-3 hafta, 2 robot, 1 depo, yerleştirme görevi, görsel doğrulama

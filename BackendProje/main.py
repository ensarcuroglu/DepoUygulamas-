import _ml_models_path  # noqa: F401  # ml_models paketini sys.path'e ekler

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

from limiter import limiter
from app.core.config import get_settings
from app.infrastructure.scheduler import RaporScheduler

# ── Birleşik exception yapısı ──
from core import (
    APIException,
    api_exception_handler,
    generic_exception_handler,
)

# Başlangıçta key yapılandırmasını logla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

# ── YENİ Clean Architecture Router'ları ──
from app.api.v1.routers import ( # noqa: E402
    urunler_router as v1_urunler_router,
    stok_hareketleri_router as v1_stok_hareketleri_router,
    siparisler_router as v1_siparisler_router,
    markalar_router as v1_markalar_router,
    kategoriler_router as v1_kategoriler_router,
    tedarikciler_router as v1_tedarikciler_router,
    depolar_router as v1_depolar_router,
    zonlar_router as v1_zonlar_router,
    raflar_router as v1_raflar_router,
    lotlar_router as v1_lotlar_router,
    paletler_router as v1_paletler_router,
    kullanicilar_router as v1_kullanicilar_router,
    destek_router as v1_destek_router,
    sistem_loglari_router as v1_sistem_loglari_router,
    irsaliyeler_router as v1_irsaliyeler_router,
    sevkiyat_planlama_router as v1_sevkiyat_planlama_router,
    stok_sayim_router as v1_stok_sayim_router,
    raporlar_router as v1_raporlar_router,
    auth_router as v1_auth_router,
    dashboard_router as v1_dashboard_router,
    mal_kabul_irsaliyeleri_router as v1_mal_kabul_irsaliyeleri_router,
    belge_taslaklari_router as v1_belge_taslaklari_router,
    mal_kabul_router as v1_mal_kabul_router,
    stok_islemleri_router as v1_stok_islemleri_router,
    yerlestirme_gorevleri_router as v1_yerlestirme_gorevleri_router,
    mobil_terminal_router as v1_mobil_terminal_router,
    toplama_gorevleri_router as v1_toplama_gorevleri_router,
    palet_rezervasyonlari_router as v1_palet_rezervasyonlari_router,
    uretim_paletleri_router as v1_uretim_paletleri_router,
    etiket_sablonlari_router as v1_etiket_sablonlari_router,
    talep_tahmini_router as v1_talep_tahmini_router,
    ai_proxy_router as v1_ai_proxy_router,
    operator_performans_router as v1_operator_performans_router,
    agv_callbacks_router as v1_agv_callbacks_router,
)

_scheduler = RaporScheduler()


def _migration_drift_kontrol() -> None:
    """Startup'ta DB şeması ile kod arasındaki Alembic uyumunu doğrular.

    Migration head'i yazılmış ama uygulanmamışsa kullanıcıya 1146 ("Table
    doesn't exist") hatası dönmeden önce burada anlamlı bir hata fırlatır.

    Çevre değişkenleriyle davranış:
      - `DEPO_SKIP_MIGRATION_CHECK=1` → kontrolü tamamen atlar (acil durum kapısı)
      - `DEPO_STRICT_MIGRATION=1`     → drift varsa RuntimeError ile boot'u durdur
        (production için önerilir; dev'de varsayılan olarak yalnız uyarı verir)
    """
    if os.environ.get("DEPO_SKIP_MIGRATION_CHECK", "").strip() == "1":
        logger.info("Migration drift kontrolü DEPO_SKIP_MIGRATION_CHECK ile atlandı.")
        return

    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from database import engine
    except Exception as exc:
        logger.warning("Migration drift kontrolü atlandı (import hatası): %s", exc)
        return

    alembic_ini = Path(__file__).resolve().parent / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("alembic.ini bulunamadı: %s — drift kontrolü atlandı.", alembic_ini)
        return

    try:
        cfg = Config(str(alembic_ini))
        script = ScriptDirectory.from_config(cfg)
        kod_head = script.get_current_head()
        with engine.connect() as conn:
            db_revision = MigrationContext.configure(conn).get_current_revision()
    except Exception as exc:
        logger.error("Migration drift kontrolü başarısız (DB erişim?): %s", exc)
        return

    if db_revision == kod_head:
        logger.info("Migration drift yok — DB head = %s", kod_head)
        return

    mesaj = (
        f"DB MIGRATION DRIFT: kod head={kod_head!r}, db revision={db_revision!r}. "
        f"`alembic upgrade head` çalıştırın. Acil durumda DEPO_SKIP_MIGRATION_CHECK=1 "
        f"ile bu kontrolü atlayabilirsiniz (önerilmez)."
    )
    if os.environ.get("DEPO_STRICT_MIGRATION", "").strip() == "1":
        logger.error(mesaj)
        raise RuntimeError(mesaj)
    logger.warning(mesaj)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _migration_drift_kontrol()
    _scheduler.start()
    # Süresi dolmuş idempotency kayıtlarını temizle
    try:
        from database import SessionLocal
        from app.core.idempotency import idempotency_temizle
        with SessionLocal() as db:
            silinen = idempotency_temizle(db)
            if silinen:
                logger.info(f"Startup: {silinen} süresi dolmuş idempotency kaydı temizlendi.")
    except Exception as e:
        logger.warning(f"Idempotency cleanup başarısız (kritik değil): {e}")
    yield
    _scheduler.shutdown()



app = FastAPI(
    title="Depo Yönetim Sistemi API",
    description="Endüstriyel depo ve stok yönetimi için RESTful API — LOT/Palet takibli",
    version="2.0.0",
    lifespan=lifespan
)

# Rate Limiter Middleware ve Exception Handler
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# ========================
# EXCEPTION HANDLER KAYITLARI
# ========================

# Birleşik handler: Tüm APIException alt sınıfları (legacy + domain) tek handler ile yakalanır
app.add_exception_handler(APIException, api_exception_handler)

# Genel fallback handler
app.add_exception_handler(Exception, generic_exception_handler)

# Özel 429 hata mesajı handler'ı
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Çok fazla istek gönderdiniz. Lütfen daha sonra tekrar deneyin.",
            "retry_after": exc.detail
        }
    )

# CORS ayarları — React'ın bu sunucuya erişebilmesi için
app.add_middleware(
    CORSMiddleware,
    # BURASI GÜNCELLENDİ: http yerine https yazmalısın
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# ROUTER KAYITLARI
# ========================

# YENİ Clean Architecture Router'ları (DI tabanlı)
app.include_router(v1_urunler_router)
app.include_router(v1_stok_hareketleri_router)
app.include_router(v1_siparisler_router)
app.include_router(v1_markalar_router)
app.include_router(v1_kategoriler_router)
app.include_router(v1_tedarikciler_router)
app.include_router(v1_depolar_router)
app.include_router(v1_zonlar_router)
app.include_router(v1_raflar_router)
app.include_router(v1_lotlar_router)
app.include_router(v1_paletler_router)
app.include_router(v1_kullanicilar_router)
app.include_router(v1_destek_router)
app.include_router(v1_sistem_loglari_router)

# CA Router'lar (Faz 3a + 3b + 3c)
app.include_router(v1_irsaliyeler_router)
app.include_router(v1_sevkiyat_planlama_router)
app.include_router(v1_stok_sayim_router)
app.include_router(v1_raporlar_router)
app.include_router(v1_mal_kabul_irsaliyeleri_router)
app.include_router(v1_belge_taslaklari_router)
app.include_router(v1_mal_kabul_router)
app.include_router(v1_stok_islemleri_router)
app.include_router(v1_yerlestirme_gorevleri_router)
app.include_router(v1_mobil_terminal_router)

# Faz 1 — MVP Outbound Core
app.include_router(v1_toplama_gorevleri_router)
app.include_router(v1_palet_rezervasyonlari_router)

# Faz 4 — Üretim Paleti Giriş Sistemi
app.include_router(v1_uretim_paletleri_router)

# Etiket Modülü — Şablon yönetimi
app.include_router(v1_etiket_sablonlari_router)
app.include_router(v1_talep_tahmini_router)

# Auth + Dashboard Router (CA — Faz 3d)
app.include_router(v1_auth_router)
app.include_router(v1_dashboard_router)
app.include_router(v1_ai_proxy_router)

# LMS Faz 2 — Operatör Performans (KPI okuma uçları)
app.include_router(v1_operator_performans_router)
app.include_router(v1_agv_callbacks_router)


@app.get("/")
def ana_sayfa():
    return {
        "mesaj": "Depo Yönetim Sistemi API'sine hoş geldiniz!",
        "docs": "/docs",
        "versiyon": "2.0.0"
    }

# uvicorn main:app --reload --host 127.0.0.1 --port 8000

# uvicorn main:app --host 0.0.0.0 --port 8000
# npm run dev -- --host

# AI Asistan Servisi Başlatma
# .\venv\Scripts\Activate.ps1
# uvicorn main:app --host 127.0.0.1 --port 8001 

# AVG Simülasyon Başlatma
# .\venv\Scripts\Activate.ps1
# uvicorn main:app --host 127.0.0.1 --port 8002
# komut ile istek testi
# curl -X POST http://127.0.0.1:8002/api/agv/gorevler -H "Content-Type: application/json" -d "{\"wms_gorev_id\":1,\"wms_gorev_tipi\":\"Yerlestirme\",\"kaynak_raf_id\":101,\"hedef_raf_id\":201}"

# KAMERA İZNİ İÇİN FARKLI TERMİNALLERDE ÇALIŞTIRMA KODU:
# ssh -R 80:localhost:5173 nokey@localhost.run

# LİNT HATALARI KODU 
# npm run lint 2>&1 | tee lint-hatalari.log

# RUFF HATALARI KODU
# ruff check . > ruff-check-ciktisi.log

# PYRIGHT HATALARI KODU
# pyright > pyright-hatalari.log

# Sadeleştirilmiş Terminal Çıktısı ile Hızlı Kod Kapsamı Analizi (coverage.py)
# pytest --cov=app --cov-report=term --disable-warnings -q --tb=short

# CLOUDFLARED İLE HTTPS TUNNEL AÇMA KODU (Geliştirme sırasında güvenli bağlantı için)
# & "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --protocol http2 --url https://localhost:4173 --no-tls-verify

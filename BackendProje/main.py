import _ml_models_path  # noqa: F401  # ml_models paketini sys.path'e ekler

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
    stok_islemleri_router as v1_stok_islemleri_router,
    yerlestirme_gorevleri_router as v1_yerlestirme_gorevleri_router,
    mobil_terminal_router as v1_mobil_terminal_router,
    toplama_gorevleri_router as v1_toplama_gorevleri_router,
    palet_rezervasyonlari_router as v1_palet_rezervasyonlari_router,
    uretim_paletleri_router as v1_uretim_paletleri_router,
    etiket_sablonlari_router as v1_etiket_sablonlari_router,
    talep_tahmini_router as v1_talep_tahmini_router,
)

_scheduler = RaporScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
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

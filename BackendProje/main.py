from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

from database import engine, SessionLocal
from models import Base, RaporSchedule
from auth import SECRET_KEY
from limiter import limiter

# ── Birleşik exception yapısı ──
from core import (
    APIException,
    api_exception_handler,
    generic_exception_handler,
)

# Başlangıçta key yapılandırmasını logla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"🔐 JWT Secret Key: {SECRET_KEY[:8]}... (yapılandırıldı)")

# ── YENİ Clean Architecture Router'ları ──
from app.api.v1.routers import (
    urunler_router as v1_urunler_router,
    stok_hareketleri_router as v1_stok_hareketleri_router,
    siparisler_router as v1_siparisler_router,
    markalar_router as v1_markalar_router,
    kategoriler_router as v1_kategoriler_router,
    tedarikciler_router as v1_tedarikciler_router,
    depolar_router as v1_depolar_router,
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
)

# ========================
# APScheduler Kurulumu
# ========================
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    def zamanlama_kontrol():
        """Her dakika çalışır; sırası gelen zamanlı raporları tetikler."""
        db = SessionLocal()
        try:
            simdi = datetime.utcnow()
            schedules = db.query(RaporSchedule).filter(RaporSchedule.is_aktif == True).all()
            for schedule in schedules:
                saat_str = schedule.saat or "09:00"
                try:
                    saat, dakika = int(saat_str.split(":")[0]), int(saat_str.split(":")[1])
                except Exception:
                    continue

                # Son çalıştırma kontrolü — aynı gün çalıştırılmışsa atla
                if schedule.son_calistirilma:
                    son = schedule.son_calistirilma
                    if schedule.periyod == "gunluk" and son.date() == simdi.date():
                        continue
                    elif schedule.periyod == "haftalik" and (simdi - son).days < 7:
                        continue
                    elif schedule.periyod == "aylik" and (simdi - son).days < 30:
                        continue

                # Saat uygun mu?
                if simdi.hour == saat and simdi.minute == dakika:
                    schedule.son_calistirilma = simdi
                    db.commit()
                    logger.info(f"Zamanlı rapor tetiklendi: {schedule.sablon_adi}")
                    # E-posta gönderimi (isteğe bağlı — SMTP yapılandırması gerektirir)
                    _zamanlama_email_gonder(schedule)
        except Exception as e:
            logger.error(f"Zamanlama kontrolü hatası: {e}")
        finally:
            db.close()

    def _zamanlama_email_gonder(schedule):
        """Zamanlı rapor e-postası gönderir (SMTP yapılandırılmışsa)."""
        import os
        smtp_host = os.getenv("SMTP_HOST")
        if not smtp_host:
            return  # SMTP ayarlanmamış, atla

        alicilar = schedule.alici_emailler or []
        if not alicilar:
            return

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_pass = os.getenv("SMTP_PASSWORD", "")
            smtp_from = os.getenv("SMTP_FROM", smtp_user)

            msg = MIMEMultipart()
            msg["From"] = smtp_from
            msg["To"] = ", ".join(alicilar)
            msg["Subject"] = f"Otomatik Rapor: {schedule.sablon_adi}"
            body = (
                f"Merhaba,\n\n"
                f"'{schedule.sablon_adi}' raporu ({schedule.periyod}) otomatik olarak oluşturuldu.\n"
                f"Rapor: {schedule.format.upper()} formatında hazırlanmıştır.\n\n"
                f"Depo Yönetim Sistemi"
            )
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, alicilar, msg.as_string())

            logger.info(f"E-posta gönderildi: {alicilar}")
        except Exception as e:
            logger.error(f"E-posta gönderilemedi: {e}")

    scheduler = BackgroundScheduler(timezone="Europe/Istanbul")
    scheduler.add_job(zamanlama_kontrol, CronTrigger(minute="*"))  # Her dakika kontrol
    SCHEDULER_AKTIF = True
except ImportError:
    SCHEDULER_AKTIF = False
    logger.warning("apscheduler kurulu değil — zamanlı raporlar devre dışı")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Başlangıç
    if SCHEDULER_AKTIF:
        scheduler.start()
        logger.info("APScheduler başlatıldı")
    yield
    # Kapanış
    if SCHEDULER_AKTIF:
        scheduler.shutdown()
        logger.info("APScheduler durduruldu")


# Veritabanı tablolarını oluştur (yoksa)
Base.metadata.create_all(bind=engine)

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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
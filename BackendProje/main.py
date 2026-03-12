from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from datetime import datetime
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

from database import engine, get_db, SessionLocal
from models import Base, Kullanici, RaporSchedule
from auth import get_current_user, require_role, SECRET_KEY
import crud
from schemas import DashboardStats

# Başlangıçta key yapılandırmasını logla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"🔐 JWT Secret Key: {SECRET_KEY[:8]}... (yapılandırıldı)")

# Rate Limiter yapılandırması
limiter = Limiter(key_func=get_remote_address)

# Router'ları içe aktar
from routers import (
    urunler, kategoriler, stok_hareketleri, auth,
    kullanicilar, tedarikciler, markalar, depolar, lotlar, paletler, raflar, sistem_loglari, destek,
    siparisler, sevkiyat_planlama, irsaliyeler, raporlar, stok_sayim
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

# Rate Limite Middleware ve Exception Handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Özel 429 hata mesajı handler'ı (opsiyonel, _rate_limit_exceeded_handler standardını kullanabiliriz)
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

# Router'ları kaydet
app.include_router(auth.router)
app.include_router(markalar.router)
app.include_router(urunler.router)
app.include_router(kategoriler.router)
app.include_router(depolar.router)
app.include_router(lotlar.router)
app.include_router(paletler.router)
app.include_router(raflar.router)
app.include_router(stok_hareketleri.router)
app.include_router(kullanicilar.router)
app.include_router(tedarikciler.router)
app.include_router(sistem_loglari.router)
app.include_router(destek.router)
app.include_router(siparisler.router)
app.include_router(sevkiyat_planlama.router)
app.include_router(irsaliyeler.router)
app.include_router(raporlar.router)
app.include_router(stok_sayim.router)


@app.get("/")
def ana_sayfa():
    return {
        "mesaj": "Depo Yönetim Sistemi API'sine hoş geldiniz!",
        "docs": "/docs",
        "versiyon": "2.0.0"
    }


@app.get("/api/dashboard", response_model=DashboardStats)
def dashboard_istatistikleri(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Dashboard için toplam ürün, kritik stok, günlük hareket ve toplam değer istatistikleri"""
    return crud.get_dashboard_stats(db)

# uvicorn main:app --reload --host 127.0.0.1 --port 8000
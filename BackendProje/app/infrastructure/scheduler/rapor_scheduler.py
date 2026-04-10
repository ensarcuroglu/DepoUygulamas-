"""
Zamanlı Rapor Scheduler — Infrastructure katmanı.

APScheduler ile her dakika çalışır; sırası gelen RaporSchedule
kayıtlarını tetikler ve isteğe bağlı SMTP e-postası gönderir.
"""

import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from database import SessionLocal
from models import RaporSchedule

logger = logging.getLogger(__name__)


def zamanlama_kontrol() -> None:
    """Her dakika çalışır; sırası gelen zamanlı raporları tetikler."""
    db = SessionLocal()
    try:
        simdi = datetime.utcnow()
        schedules = db.query(RaporSchedule).filter(RaporSchedule.is_aktif).all()
        for schedule in schedules:
            saat_str = schedule.saat or "09:00"
            try:
                saat_parcalari = saat_str.split(":")
                saat = int(saat_parcalari[0])
                dakika = int(saat_parcalari[1])
                if not (0 <= saat <= 23 and 0 <= dakika <= 59):
                    logger.warning(
                        "Geçersiz zamanlama saati atlandı. schedule_id=%s saat=%r",
                        schedule.id,
                        saat_str,
                    )
                    continue
            except (ValueError, IndexError):
                logger.warning(
                    "Zaman formatı çözümlenemedi, kayıt atlandı. schedule_id=%s saat=%r",
                    schedule.id,
                    saat_str,
                )
                continue

            # Son çalıştırma kontrolü — aynı periyotta çalıştırılmışsa atla
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
                logger.info("Zamanlı rapor tetiklendi: %s", schedule.sablon_adi)
                _zamanlama_email_gonder(schedule)
    except Exception as e:
        logger.error("Zamanlama kontrolü hatası: %s", e)
    finally:
        db.close()


def _zamanlama_email_gonder(schedule: RaporSchedule) -> None:
    """Zamanlı rapor e-postası gönderir (SMTP yapılandırılmışsa)."""
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        return

    alicilar = schedule.alici_emailler or []
    if not alicilar:
        return

    try:
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

        logger.info("E-posta gönderildi: %s", alicilar)
    except Exception as e:
        logger.error("E-posta gönderilemedi: %s", e)
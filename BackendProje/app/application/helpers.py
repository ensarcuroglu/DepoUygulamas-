"""
Application katmanı yardımcı fonksiyonları.

ORM model veya domain entity farketmeksizin ortak kontroller.
"""

from app.core.entities.kullanici import KullaniciRol


def admin_mi(user) -> bool:
    """Kullanıcının admin olup olmadığını kontrol eder.

    ORM model (models.Kullanici) veya domain entity (core.entities.Kullanici)
    farketmeksizin çalışır — duck typing ile 'rol' attribute'ına bakar.
    """
    return getattr(user, "rol", None) == KullaniciRol.ADMIN

"""
Birlesik Exception Hiyerarsisi
==============================

Hem legacy (APIException) hem de domain (eski DomainException) exception'larini
tek bir hiyerarsi altinda toplar.

Legacy exception'lar (NotFoundError, DuplicateError, vb.) ve domain exception'lar
(KayitBulunamadiError, YetersizStokError, vb.) hepsi APIException'dan turemistir.
Boylece tek bir handler yeterlidir.

Ileride Clean Architecture gecisinde domain exception'lar ayri bir module tasinabilir;
su an icin hepsi ayni base class'tan turemektedir.
"""
from fastapi import status
from typing import Any, Optional


class APIException(Exception):
    """Base API exception - tum ozel hatalarin atasi."""

    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    @property
    def mesaj(self) -> str:
        """Geriye donuk uyumluluk: eski DomainException kodlari exc.mesaj kullaniyor."""
        return self.message


# =====================================================================
# LEGACY EXCEPTION'LAR (mevcut 15 modul icin)
# =====================================================================

class NotFoundError(APIException):
    """Kaynak bulunamadi (404)"""

    def __init__(self, resource: str, resource_id: Any):
        message = f"{resource} (ID: {resource_id}) bulunamadı"
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            message,
            {"resource": resource, "id": str(resource_id)},
        )


class InputValidationError(APIException):
    """Giris validasyonu hatasi (422)
    Not: Pydantic'in ValidationError'i ile cakismamasi icin bu adi kullaniyoruz.
    """

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message, details)


class DuplicateError(APIException):
    """Mukerrer kayit hatasi (409)"""

    def __init__(self, field: str, value: str):
        message = f"{field} '{value}' zaten mevcut"
        super().__init__(
            status.HTTP_409_CONFLICT,
            message,
            {"field": field, "value": value},
        )


class PermissionDeniedError(APIException):
    """Yetki hatasi (403)"""

    def __init__(self, message: str = "Bu işlemi yapmaya yetkiniz yok"):
        super().__init__(status.HTTP_403_FORBIDDEN, message)


class AuthenticationError(APIException):
    """Kimlik dogrulama hatasi (401)"""

    def __init__(self, message: str = "Kimlik doğrulama başarısız"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)


class BadRequestError(APIException):
    """Gecersiz istek hatasi (400)"""

    def __init__(self, message: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, message)


# =====================================================================
# DOMAIN EXCEPTION'LAR (Clean Architecture modulleri icin)
# =====================================================================

class KayitBulunamadiError(APIException):
    """Istenen kayit veritabaninda bulunamadi."""

    def __init__(self, entity_adi: str, entity_id: int | str | None = None):
        self.entity_adi = entity_adi
        self.entity_id = entity_id
        mesaj = f"{entity_adi} bulunamadı"
        if entity_id is not None:
            mesaj += f" (ID: {entity_id})"
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            mesaj,
            {"entity": entity_adi, "id": str(entity_id) if entity_id else None},
        )


class YetkisizIslemError(APIException):
    """Kullanicinin bu islem icin yetkisi yok."""

    def __init__(self, mesaj: str = "Bu işlem için yetkiniz bulunmamaktadır."):
        super().__init__(status.HTTP_403_FORBIDDEN, mesaj)


class YetersizStokError(APIException):
    """Stok cikisi icin yeterli miktar yok."""

    def __init__(self, urun_ismi: str, mevcut: int, istenen: int):
        self.urun_ismi = urun_ismi
        self.mevcut = mevcut
        self.istenen = istenen
        mesaj = f"Yetersiz stok! Ürün: {urun_ismi}, Mevcut: {mevcut}, İstenen: {istenen}"
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            mesaj,
            {"urun": urun_ismi, "mevcut": mevcut, "istenen": istenen},
        )


class StokVeriUyumsuzluguError(APIException):
    """Palet toplamlari ile beklenen stok eslesmiyur."""

    def __init__(self, urun_ismi: str):
        mesaj = f"Stok veri uyuşmazlığı: {urun_ismi}"
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            mesaj,
            {"urun": urun_ismi},
        )


class GecersizDurumGecisiError(APIException):
    """Durum makinesi gecersiz gecis."""

    def __init__(self, entity_adi: str, mevcut: str, hedef: str):
        mesaj = f"{entity_adi} için geçersiz durum geçişi: {mevcut} → {hedef}"
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            mesaj,
            {"entity": entity_adi, "mevcut_durum": mevcut, "hedef_durum": hedef},
        )


class CakismaHatasi(APIException):
    """Benzersiz kisitlama ihlali (duplicate kayit vb.)."""

    def __init__(self, alan: str, deger: str):
        self.alan = alan
        self.deger = deger
        mesaj = f"Bu {alan} zaten kullanılıyor: {deger}"
        super().__init__(
            status.HTTP_409_CONFLICT,
            mesaj,
            {"field": alan, "value": deger},
        )


class GecersizIslemError(APIException):
    """Genel is kurali ihlali."""

    def __init__(self, message: str = "Geçersiz işlem."):
        super().__init__(status.HTTP_400_BAD_REQUEST, message)


class DepoErisimHatasi(APIException):
    """Kullanicinin hedef depoya erisim yetkisi yok."""

    def __init__(self, kullanici_depo_id: int | None, hedef_depo_id: int, depo_adi: str = ""):
        self.kullanici_depo_id = kullanici_depo_id
        self.hedef_depo_id = hedef_depo_id
        if depo_adi:
            mesaj = f"Bu palet {depo_adi} deposuna ait, yetkiniz bulunmuyor."
        else:
            mesaj = f"Bu palet farklı bir depoya ait (Depo ID: {hedef_depo_id}), yetkiniz bulunmuyor."
        super().__init__(
            status.HTTP_403_FORBIDDEN,
            mesaj,
            {"kullanici_depo_id": kullanici_depo_id, "hedef_depo_id": hedef_depo_id},
        )

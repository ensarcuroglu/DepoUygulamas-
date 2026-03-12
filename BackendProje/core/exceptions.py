"""
Custom Exception Sınıfları
Tüm API exception'ları bu dosyadan import edilecek.

Düzeltmeler (plan1.md'den):
  - ValidationError → InputValidationError (Pydantic ile isim çakışmasını önler)
  - NotFoundError.resource_id: Any (barkod gibi string ID'leri de destekler)
"""
from fastapi import status
from typing import Any, Optional


class APIException(Exception):
    """Base API exception — tüm özel hataların atası"""

    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(APIException):
    """Kaynak bulunamadı (404)"""

    def __init__(self, resource: str, resource_id: Any):
        message = f"{resource} (ID: {resource_id}) bulunamadı"
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            message,
            {"resource": resource, "id": str(resource_id)},
        )


class InputValidationError(APIException):
    """Giriş validasyonu hatası (422)
    Not: Pydantic'in ValidationError'ı ile çakışmaması için bu adı kullanıyoruz.
    """

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message, details)


class DuplicateError(APIException):
    """Mükerrer kayıt hatası (409)"""

    def __init__(self, field: str, value: str):
        message = f"{field} '{value}' zaten mevcut"
        super().__init__(
            status.HTTP_409_CONFLICT,
            message,
            {"field": field, "value": value},
        )


class PermissionDeniedError(APIException):
    """Yetki hatası (403)"""

    def __init__(self, message: str = "Bu işlemi yapmaya yetkiniz yok"):
        super().__init__(status.HTTP_403_FORBIDDEN, message)


class AuthenticationError(APIException):
    """Kimlik doğrulama hatası (401)"""

    def __init__(self, message: str = "Kimlik doğrulama başarısız"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)


class BadRequestError(APIException):
    """Geçersiz istek hatası (400)"""

    def __init__(self, message: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, message)

"""
Legacy exception modulu — geriye donuk uyumluluk icin korunmaktadir.

Asil tanim core.api_exceptions'dadır.
Mevcut services/*.py ve routers/*.py dosyalari bu dosyayi import etmeye
devam edebilir.
"""

from .api_exceptions import (
    APIException,
    NotFoundError,
    InputValidationError,
    DuplicateError,
    PermissionDeniedError,
    AuthenticationError,
    BadRequestError,
)

__all__ = [
    "APIException",
    "NotFoundError",
    "InputValidationError",
    "DuplicateError",
    "PermissionDeniedError",
    "AuthenticationError",
    "BadRequestError",
]

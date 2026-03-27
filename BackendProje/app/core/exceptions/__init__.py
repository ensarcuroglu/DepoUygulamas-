"""
Domain-level exceptions — artik core.api_exceptions'dan turemektedir.

Bu dosya geriye donuk uyumluluk icin korunmaktadir.
Use case'ler ve diger Clean Architecture modulleri bu dosyayi import etmeye
devam edebilir; asil tanim core.api_exceptions'dadır.
"""

from core.api_exceptions import (
    APIException,
    KayitBulunamadiError,
    YetkisizIslemError,
    YetersizStokError,
    StokVeriUyumsuzluguError,
    GecersizDurumGecisiError,
    CakismaHatasi,
    GecersizIslemError,
    DepoErisimHatasi,
)

# Geriye donuk uyumluluk: eski DomainException referanslarini APIException'a yonlendir
DomainException = APIException

__all__ = [
    "DomainException",
    "KayitBulunamadiError",
    "YetkisizIslemError",
    "YetersizStokError",
    "StokVeriUyumsuzluguError",
    "GecersizDurumGecisiError",
    "CakismaHatasi",
    "GecersizIslemError",
    "DepoErisimHatasi",
]

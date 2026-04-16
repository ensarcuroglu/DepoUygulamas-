"""
Uygulama genelinde kullanılan sabit değerler (Constants).
Magic string'leri önlemek ve statik kod analizi uyarılarını çözmek için kullanılır.

Not: Bandit B105 kuralı, değişken isimlerindeki 'TOKEN' vb. kelimelerden dolayı
aşağıdaki standart tipleri hardcoded şifre zannederek 'False Positive' üretmektedir.
Bu değerler şifre olmadığı için sadece bu dosyada bilinçli olarak (# nosec B105) ile susturulmuştur.
"""

class AuthConstants:
    BEARER_TOKEN_TYPE = "bearer"    # nosec B105
    ACCESS_TOKEN_TYPE = "access"    # nosec B105
    REFRESH_TOKEN_TYPE = "refresh"  # nosec B105
    BCRYPT_ALGORITHM = "bcrypt"     # nosec B105


class PaletKaynakSabit:
    """Palet kaynak tipleri."""
    URETIM = "uretim"
    IRSALIYE = "irsaliye"
    ERP = "erp"
    MANUEL = "manuel"

    _KAYNAKLAR = {URETIM, IRSALIYE, ERP, MANUEL}

    @classmethod
    def gecerli_mi(cls, kaynak: str) -> bool:
        return kaynak in cls._KAYNAKLAR
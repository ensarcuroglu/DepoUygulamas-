"""Domain-level exceptions — framework bağımsız."""


class DomainException(Exception):
    """Tüm domain hatalarının base class'ı."""

    def __init__(self, mesaj: str = "Bir hata oluştu."):
        self.mesaj = mesaj
        super().__init__(self.mesaj)


# ── Bulunamadı Hataları ──

class KayitBulunamadiError(DomainException):
    """İstenen kayıt veritabanında bulunamadı."""

    def __init__(self, entity_adi: str, entity_id: int | str | None = None):
        self.entity_adi = entity_adi
        self.entity_id = entity_id
        mesaj = f"{entity_adi} bulunamadı"
        if entity_id is not None:
            mesaj += f" (ID: {entity_id})"
        super().__init__(mesaj)


# ── Yetki Hataları ──

class YetkisizIslemError(DomainException):
    """Kullanıcının bu işlem için yetkisi yok."""

    def __init__(self, mesaj: str = "Bu işlem için yetkiniz bulunmamaktadır."):
        super().__init__(mesaj)


# ── Stok Hataları ──

class YetersizStokError(DomainException):
    """Stok çıkışı için yeterli miktar yok."""

    def __init__(self, urun_ismi: str, mevcut: int, istenen: int):
        self.urun_ismi = urun_ismi
        self.mevcut = mevcut
        self.istenen = istenen
        super().__init__(
            f"Yetersiz stok! Ürün: {urun_ismi}, Mevcut: {mevcut}, İstenen: {istenen}"
        )


class StokVeriUyumsuzluguError(DomainException):
    """Palet toplamları ile beklenen stok eşleşmiyor."""

    def __init__(self, urun_ismi: str):
        super().__init__(f"Stok veri uyuşmazlığı: {urun_ismi}")


# ── İş Kuralı İhlalleri ──

class GecersizDurumGecisiError(DomainException):
    """Durum makinesi geçersiz geçiş."""

    def __init__(self, entity_adi: str, mevcut: str, hedef: str):
        super().__init__(
            f"{entity_adi} için geçersiz durum geçişi: {mevcut} → {hedef}"
        )


class CakismaHatasi(DomainException):
    """Benzersiz kısıtlama ihlali (duplicate kayıt vb.)."""

    def __init__(self, alan: str, deger: str):
        self.alan = alan
        self.deger = deger
        super().__init__(f"Bu {alan} zaten kullanılıyor: {deger}")


class GecersizIslemError(DomainException):
    """Genel iş kuralı ihlali."""
    pass

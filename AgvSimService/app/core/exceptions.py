"""AGV simülasyon domain exception'ları."""


class AgvDomainError(Exception):
    """Tüm AGV domain hatalarının base sınıfı."""


class GecersizDurumGecisi(AgvDomainError):
    def __init__(self, mevcut: str, hedef: str) -> None:
        super().__init__(f"Geçersiz robot durum geçişi: {mevcut} → {hedef}")
        self.mevcut = mevcut
        self.hedef = hedef


class RotaBulunamadi(AgvDomainError):
    pass


class GridDisinda(AgvDomainError):
    pass

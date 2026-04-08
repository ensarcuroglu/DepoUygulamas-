from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class KapasiteSonuc:
    """Kapasite kontrol sonucu value object."""
    yeterli: bool
    neden: Optional[str] = None  # "Hacim Limiti Aşıldı" veya "Ağırlık Limiti Aşıldı"


@dataclass
class Raf:
    """Raf (shelf/rack) domain entity."""

    id: Optional[int] = None
    depo_id: Optional[int] = None
    zon_id: Optional[int] = None          # Bağlı zon (Faz 0.2+)
    kod: str = ""
    bolge: str = ""                        # DEPRECATED: yeni akışlarda zon_id kullanılır
    kapasite: int = 100
    max_agirlik_kg: Optional[float] = None  # Maksimum ağırlık kapasitesi
    koridor: str = ""                       # Koridor kodu (ör: "A", "B")
    kat: int = 0                            # Kat numarası
    goz: int = 0                            # Göz numarası
    aktif: bool = True
    is_staging: bool = False                 # MIGRATION_STAGING rafı explicit bayrağı
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def deaktif_et(self) -> None:
        self.aktif = False

    def aktif_et(self) -> None:
        self.aktif = True

    def kapasite_yeterli_mi(
        self,
        mevcut_palet_sayisi: int,
        mevcut_agirlik_kg: float = 0.0,
        yeni_palet_kg: float = 0.0,
    ) -> KapasiteSonuc:
        """Hibrit kapasite kontrolü: hem slot hem ağırlık."""
        if mevcut_palet_sayisi >= self.kapasite:
            return KapasiteSonuc(yeterli=False, neden="Hacim Limiti Aşıldı")
        if self.max_agirlik_kg and (mevcut_agirlik_kg + yeni_palet_kg) > self.max_agirlik_kg:
            return KapasiteSonuc(yeterli=False, neden="Ağırlık Limiti Aşıldı")
        return KapasiteSonuc(yeterli=True)

    # ── Hiyerarşik Kod Yardımcıları ──

    @staticmethod
    def kod_olustur(zon_kod: str, koridor: str, raf_no: int, kat: int, goz: int) -> str:
        """Hiyerarşik raf kodu oluşturur: ZON-KORIDOR-RAF-KAT-GOZ"""
        return f"{zon_kod}-{koridor}-{raf_no:02d}-{kat:02d}-{goz:02d}"

    @staticmethod
    def kod_parse(kod: str) -> dict:
        """Raf kodunu parse eder.
        Returns: {"zon_kod": "GNL", "koridor": "A", "raf_no": 12, "kat": 1, "goz": 1}
        Raises: ValueError — geçersiz format (5 segment beklenir)
        """
        parcalar = kod.split("-")
        if len(parcalar) != 5:
            raise ValueError(
                f"Geçersiz raf kodu formatı: {kod}. Beklenen: ZON-KORIDOR-RAF-KAT-GOZ"
            )
        return {
            "zon_kod": parcalar[0],
            "koridor": parcalar[1],
            "raf_no": int(parcalar[2]),
            "kat": int(parcalar[3]),
            "goz": int(parcalar[4]),
        }

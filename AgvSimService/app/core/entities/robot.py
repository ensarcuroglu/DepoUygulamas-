"""Robot domain entity + state machine.

Tasarım notu: WMS'in `YerlestirmeGorevi` desenini birebir taklit eder
(`_GECISLER` dict + `_durum_gecisi`).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.core.entities.path import Path
from app.core.exceptions import GecersizDurumGecisi


class RobotDurum(str, Enum):
    BOS = "Bos"
    KAYNAGA_GIDIYOR = "KaynagaGidiyor"
    YUKLUYOR = "Yukluyor"
    TASIYOR = "Tasiyor"
    BIRAKIYOR = "Birakiyor"
    TAMAMLANDI_BILDIRIM = "TamamlandiBildirim"
    HATA_DURUYOR = "HataDuruyor"


_GECISLER: dict[RobotDurum, set[RobotDurum]] = {
    RobotDurum.BOS: {RobotDurum.KAYNAGA_GIDIYOR, RobotDurum.HATA_DURUYOR},
    RobotDurum.KAYNAGA_GIDIYOR: {RobotDurum.YUKLUYOR, RobotDurum.HATA_DURUYOR},
    RobotDurum.YUKLUYOR: {RobotDurum.TASIYOR, RobotDurum.HATA_DURUYOR},
    RobotDurum.TASIYOR: {RobotDurum.BIRAKIYOR, RobotDurum.HATA_DURUYOR},
    RobotDurum.BIRAKIYOR: {RobotDurum.TAMAMLANDI_BILDIRIM, RobotDurum.HATA_DURUYOR},
    RobotDurum.TAMAMLANDI_BILDIRIM: {RobotDurum.BOS, RobotDurum.HATA_DURUYOR},
    RobotDurum.HATA_DURUYOR: {RobotDurum.BOS},
}


# Yükleme/bırakma sürelerini tick cinsinden tutuyoruz (gerçek-zamandan bağımsız).
YUKLEME_TICK = 2
BIRAKMA_TICK = 2


class Yon(str, Enum):
    KUZEY = "K"
    GUNEY = "G"
    DOGU = "D"
    BATI = "B"


_YON_HARITASI: dict[tuple[int, int], Yon] = {
    (0, -1): Yon.KUZEY,
    (0, 1): Yon.GUNEY,
    (1, 0): Yon.DOGU,
    (-1, 0): Yon.BATI,
}


@dataclass
class Robot:
    id: str
    x: int
    y: int
    durum: RobotDurum = RobotDurum.BOS
    yon: Yon = Yon.KUZEY
    rota: Optional[Path] = None
    aktif_gorev_id: Optional[str] = None
    bekleme_kalani: int = 0   # YUKLUYOR / BIRAKIYOR sırasında geri sayım

    def durum_gecisi(self, hedef: RobotDurum) -> None:
        if hedef not in _GECISLER.get(self.durum, set()):
            raise GecersizDurumGecisi(mevcut=self.durum.value, hedef=hedef.value)
        self.durum = hedef

    def yon_guncelle(self, dx: int, dy: int) -> None:
        yeni_yon = _YON_HARITASI.get((dx, dy))
        if yeni_yon is not None:
            self.yon = yeni_yon

    def hata_durumuna_al(self) -> None:
        # HATA_DURUYOR'a her durumdan geçilebilir (TAMAMLANDI_BILDIRIM'den de)
        # Operatör reset'i için ayrı `sifirla` çağrılmalı.
        self.durum = RobotDurum.HATA_DURUYOR
        self.rota = None
        self.bekleme_kalani = 0

    def sifirla(self) -> None:
        """HATA_DURUYOR'dan operatör müdahalesi ile BOS'a dönüş."""
        if self.durum != RobotDurum.HATA_DURUYOR:
            raise GecersizDurumGecisi(mevcut=self.durum.value, hedef=RobotDurum.BOS.value)
        self.durum = RobotDurum.BOS
        self.aktif_gorev_id = None
        self.rota = None
        self.bekleme_kalani = 0

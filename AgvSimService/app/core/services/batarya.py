"""Batarya simülasyonu — Faz 5.

Saf fonksiyonlar; her tick TickUseCase tarafından çağrılır.

Davranış:
- Hareket halindeyken (KAYNAGA_GIDIYOR/TASIYOR) tick başına `BATARYA_HAREKET`
  oranında azalır.
- Diğer durumlarda (YUKLUYOR/BIRAKIYOR/BOS uzakta) tick başına
  `BATARYA_BOSTA` azalır.
- Robot SARJ tipindeki bir hücredeyse ve durumu BOS ise her tick
  `BATARYA_DOLUYOR` oranında dolar (max 100).
- `BATARYA_KRITIK` (varsayılan %20) altına düşen BOS robot, en yakın SARJ
  konumuna otomatik rota planlar (`sarja_donuyor=True`).
- `BATARYA_OTONOM_ESIK` (varsayılan %15) altında robot HATA_DURUYOR'a düşer
  (operatör müdahalesi gerekli).

Sayılar yüzde biriminden, float (yüksek hassasiyet için).
"""

from __future__ import annotations

from app.core.entities.grid import Cell, CellTipi
from app.core.entities.robot import Robot, RobotDurum

# Tick başına yüzde değişimi
BATARYA_HAREKET = 0.10     # her hareket tick'inde -%0.1
BATARYA_BOSTA = 0.02       # bekleme/idle -%0.02
BATARYA_DOLUYOR = 0.80     # SARJ'da +%0.8

# Eşikler
BATARYA_KRITIK = 20.0      # bu altında BOS robot otomatik şarja gider
BATARYA_OTONOM_ESIK = 5.0  # bu altında robot devre dışı (HATA_DURUYOR)
BATARYA_DOLU_ESIK = 99.0   # şarjdan ayrılma için yeter eşik


_HAREKET_HALI = {RobotDurum.KAYNAGA_GIDIYOR, RobotDurum.TASIYOR}


def tick_uygula(robot: Robot, hucre_tipi: CellTipi) -> None:
    """Robotun bataryasını bir tick için günceller (state in-place)."""
    if robot.durum == RobotDurum.HATA_DURUYOR:
        return  # hata durumundayken simüle etmiyoruz

    # Şarj noktasında ve BOS isen dolduralım
    if robot.durum == RobotDurum.BOS and hucre_tipi == CellTipi.SARJ:
        robot.batarya_yuzde = min(100.0, robot.batarya_yuzde + BATARYA_DOLUYOR)
        if robot.batarya_yuzde >= BATARYA_DOLU_ESIK:
            robot.sarja_donuyor = False
        return

    # Tüketim
    if robot.durum in _HAREKET_HALI:
        robot.batarya_yuzde = max(0.0, robot.batarya_yuzde - BATARYA_HAREKET)
    else:
        robot.batarya_yuzde = max(0.0, robot.batarya_yuzde - BATARYA_BOSTA)


def en_yakin_sarj(robot: Robot, sarj_konumlari: list[Cell]) -> Cell | None:
    """Manhattan mesafesine göre en yakın SARJ hücresi."""
    if not sarj_konumlari:
        return None
    return min(
        sarj_konumlari,
        key=lambda c: abs(c.x - robot.x) + abs(c.y - robot.y),
    )

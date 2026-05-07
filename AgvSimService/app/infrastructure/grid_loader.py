"""Grid loader — JSON dosyasından Grid üretir.

Faz 2+: BackendProje API'sından depo+raf bilgisi çekme buraya eklenecek.
"""

from __future__ import annotations

import json
from pathlib import Path as FsPath

from app.core.entities.grid import Cell, CellTipi, Grid, RafKonumu


def gridi_jsondan_yukle(path: str | FsPath) -> Grid:
    """JSON şeması:

    ```json
    {
      "genislik": 20,
      "yukseklik": 10,
      "raflar": [
        {"raf_id": 1, "kod": "A-01", "x": 1, "y": 1, "yaklasma_x": 1, "yaklasma_y": 2}
      ],
      "engeller": [{"x": 0, "y": 0}],
      "sarj_konumlari": [{"x": 0, "y": 9}]
    }
    ```
    """
    veri = json.loads(FsPath(path).read_text(encoding="utf-8"))
    genislik = int(veri["genislik"])
    yukseklik = int(veri["yukseklik"])

    hucreler: list[list[CellTipi]] = [
        [CellTipi.BOS for _ in range(genislik)] for _ in range(yukseklik)
    ]

    raflar: dict[int, RafKonumu] = {}
    for raf in veri.get("raflar", []):
        x = int(raf["x"])
        y = int(raf["y"])
        if not (0 <= x < genislik and 0 <= y < yukseklik):
            raise ValueError(f"Raf {raf.get('raf_id')} grid dışında: ({x},{y})")
        hucreler[y][x] = CellTipi.RAF
        raflar[int(raf["raf_id"])] = RafKonumu(
            raf_id=int(raf["raf_id"]),
            x=x,
            y=y,
            yaklasma_x=int(raf["yaklasma_x"]),
            yaklasma_y=int(raf["yaklasma_y"]),
            kod=str(raf.get("kod", "")),
        )

    for engel in veri.get("engeller", []):
        ex, ey = int(engel["x"]), int(engel["y"])
        if 0 <= ex < genislik and 0 <= ey < yukseklik:
            hucreler[ey][ex] = CellTipi.ENGEL

    sarj_konumlari: list[Cell] = []
    for sarj in veri.get("sarj_konumlari", []):
        sx, sy = int(sarj["x"]), int(sarj["y"])
        if 0 <= sx < genislik and 0 <= sy < yukseklik:
            hucreler[sy][sx] = CellTipi.SARJ
            sarj_konumlari.append(Cell(sx, sy))

    return Grid(
        genislik=genislik,
        yukseklik=yukseklik,
        hucreler=hucreler,
        raflar=raflar,
        sarj_konumlari=sarj_konumlari,
    )

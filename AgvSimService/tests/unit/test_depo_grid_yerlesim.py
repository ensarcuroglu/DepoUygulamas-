"""data/depo_1_grid.json yerleşim doğrulama testi (grid optimizasyonu).

Bu test başlangıç durumunda hiçbir varlığın çakışmadığını ve tüm rafların
yaklaşma noktalarının geçilebilir olduğunu kontrol eder. JSON şeması veya
grid mantığı değiştirilirse bu test güncel kalmalıdır.
"""

from __future__ import annotations

import json
from pathlib import Path as FsPath

import pytest

from app.core.entities.grid import Cell, CellTipi
from app.infrastructure.grid_loader import gridi_jsondan_yukle

GRID_PATH = "data/depo_1_grid.json"


@pytest.fixture(scope="module")
def grid():
    return gridi_jsondan_yukle(GRID_PATH)


@pytest.fixture(scope="module")
def veri():
    return json.loads(FsPath(GRID_PATH).read_text(encoding="utf-8"))


# ── Boyut + sınır kontrolü ─────────────────────────────────────────


def test_grid_minimum_boyut(grid):
    """En az 40x24 olmalı (gereksinim)."""
    assert grid.genislik >= 40
    assert grid.yukseklik >= 24


def test_cevre_duvari_kapali(grid):
    """4 kenarın tamamı ENGEL olmalı — robotlar dışarı taşamaz."""
    for x in range(grid.genislik):
        assert grid.cell_tipi(Cell(x, 0)) == CellTipi.ENGEL, f"üst kenar açık: x={x}"
        assert grid.cell_tipi(Cell(x, grid.yukseklik - 1)) == CellTipi.ENGEL, (
            f"alt kenar açık: x={x}"
        )
    for y in range(grid.yukseklik):
        assert grid.cell_tipi(Cell(0, y)) == CellTipi.ENGEL, f"sol kenar açık: y={y}"
        assert grid.cell_tipi(Cell(grid.genislik - 1, y)) == CellTipi.ENGEL, (
            f"sağ kenar açık: y={y}"
        )


# ── Hücre çakışmaları ──────────────────────────────────────────────


def test_hicbir_hucre_iki_farkli_tipte_degil(veri):
    """RAF / ENGEL / SARJ aynı (x,y) çiftine ikinci kez atanmamalı."""
    isaretli: dict[tuple[int, int], str] = {}

    def kayit(x: int, y: int, tip: str) -> None:
        k = (x, y)
        assert k not in isaretli, (
            f"({x},{y}) zaten {isaretli[k]} — ikinci kez {tip} olarak işaretlendi"
        )
        isaretli[k] = tip

    for r in veri["raflar"]:
        kayit(r["x"], r["y"], f"RAF#{r['raf_id']}")
    for e in veri["engeller"]:
        kayit(e["x"], e["y"], "ENGEL")
    for s in veri["sarj_konumlari"]:
        kayit(s["x"], s["y"], "SARJ")


def test_robot_baslangic_konumlari_bos_hucrede(veri, grid):
    """Robotlar SARJ üzerinde DEĞİL, BOS hücreye yerleştirilmiş olmalı."""
    konumlar = veri.get("_baslangic_robot_konumlari", [])
    assert len(konumlar) >= 4, "En az 4 robot tanımı bekleniyor"

    gorulen: set[tuple[int, int]] = set()
    for k in konumlar:
        cell = Cell(int(k["x"]), int(k["y"]))
        # Robotlar arası çakışma yok
        anahtar = (cell.x, cell.y)
        assert anahtar not in gorulen, f"İki robot aynı hücrede: {cell}"
        gorulen.add(anahtar)
        # Hücre BOS olmalı (RAF / SARJ / ENGEL üzerinde robot olmaz)
        tip = grid.cell_tipi(cell)
        assert tip == CellTipi.BOS, (
            f"Robot {k['id']} {cell} hücresinde — beklenen BOS, gerçek {tip.value}"
        )


# ── Şarj istasyonları ──────────────────────────────────────────────


def test_sarj_istasyonlari_dogru_konumda(grid):
    """4 adet SARJ + her biri y=22'de + aralıklı (Δx≥3)."""
    sarjlar = grid.sarj_konumlari
    assert len(sarjlar) == 4
    for s in sarjlar:
        assert s.y == 22, f"Şarj y=22'de değil: {s}"
        assert grid.cell_tipi(s) == CellTipi.SARJ
    xler = sorted(s.x for s in sarjlar)
    farklar = [b - a for a, b in zip(xler, xler[1:])]
    assert all(f >= 3 for f in farklar), f"Şarj istasyonları çok yakın: x={xler}"


def test_sarj_kuzey_komsusu_gecilebilir(grid):
    """Robot şarj'a kuzeyden yanaşır → o hücre BOS/SARJ olmalı."""
    for s in grid.sarj_konumlari:
        kuzey = Cell(s.x, s.y - 1)
        assert grid.gecilebilir_mi(kuzey), (
            f"Şarj {s} kuzeyi {kuzey} engel — robot yanaşamaz"
        )


# ── Raflar + yaklaşma noktaları ────────────────────────────────────


def test_raf_sayisi_14(grid):
    assert len(grid.raflar) == 14


def test_tum_raf_yaklasma_noktalari_gecilebilir(grid):
    """Her rafın yaklaşma hücresi BOS veya SARJ tipinde olmalı; aksi halde
    görev oluşturulduğunda CA* başlangıçta None döner."""
    for raf in grid.raflar.values():
        yaklasma = Cell(raf.yaklasma_x, raf.yaklasma_y)
        assert grid.icinde_mi(yaklasma), (
            f"Raf {raf.raf_id} yaklaşması {yaklasma} grid dışında"
        )
        assert grid.gecilebilir_mi(yaklasma), (
            f"Raf {raf.raf_id} ({raf.kod}) yaklaşma hücresi {yaklasma} engel — "
            f"tipi: {grid.cell_tipi(yaklasma).value}"
        )


def test_raf_hucresi_RAF_tipinde(grid):
    for raf in grid.raflar.values():
        assert grid.cell_tipi(Cell(raf.x, raf.y)) == CellTipi.RAF


def test_raf_yaklasma_komsulugunda(grid):
    """Yaklaşma cell'i raf'ın 4-yön komşusu olmalı (manhattan=1)."""
    for raf in grid.raflar.values():
        d = abs(raf.x - raf.yaklasma_x) + abs(raf.y - raf.yaklasma_y)
        assert d == 1, (
            f"Raf {raf.raf_id} yaklaşma cell'i 4-yön komşu değil "
            f"(raf=({raf.x},{raf.y}), yaklasma=({raf.yaklasma_x},{raf.yaklasma_y}))"
        )


# ── Koridor genişliği (mesafe sanity) ──────────────────────────────


def test_ana_koridor_en_az_4_satir(grid):
    """Üst ana koridor (raf bloklarının üstü) en az 4 satır boş hücre içermeli."""
    # İlk raf bloğunun y'sini bul
    en_kucuk_raf_y = min(raf.y for raf in grid.raflar.values())
    # 0=duvar olduğu için 1..(en_kucuk_raf_y - 1) tamamen BOS olmalı
    bos_satir_sayisi = en_kucuk_raf_y - 1
    assert bos_satir_sayisi >= 4, (
        f"Ana koridor sadece {bos_satir_sayisi} satır geniş — en az 4 olmalı"
    )

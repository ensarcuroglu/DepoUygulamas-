from __future__ import annotations

from datetime import date, timedelta
from statistics import mean
from typing import Optional

from app.application.dto.talep_tahmini_dto import (
    GunlukTahminDTO,
    GunlukTalepDTO,
    TalepTahminResponseDTO,
    TalepTahminUrunOzetDTO,
    TalepTrendDTO,
)
from app.core.exceptions import KayitBulunamadiError
from app.core.repositories.talep_tahmini_repository import ITalepTahminiRepository


class TalepTahminUrunleriListeleUseCase:
    def __init__(self, repo: ITalepTahminiRepository):
        self._repo = repo

    def execute(
        self,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> list[TalepTahminUrunOzetDTO]:
        limit = max(1, min(limit, 200))
        return [
            TalepTahminUrunOzetDTO(
                id=urun.id,
                isim=urun.isim,
                barkod=urun.barkod,
                min_stok=urun.min_stok,
                stok_miktari=urun.stok_miktari,
            )
            for urun in self._repo.urunleri_listele(limit=limit, search=search)
        ]


class TalepTahminiGetirUseCase:
    def __init__(self, repo: ITalepTahminiRepository):
        self._repo = repo

    def execute(self, urun_id: int, tahmin_gun: int = 7) -> TalepTahminResponseDTO:
        urun = self._repo.urun_getir(urun_id)
        if urun is None:
            raise KayitBulunamadiError("Urun", urun_id)

        bitis = date.today()
        baslangic = bitis - timedelta(days=89)
        gunluk_cikislar = self._repo.gunluk_cikislari_getir(urun_id, baslangic, bitis)
        cikis_by_date = {item.tarih: item.miktar for item in gunluk_cikislar}

        gecmis_seri = [
            GunlukTalepDTO(
                tarih=baslangic + timedelta(days=offset),
                miktar=float(cikis_by_date.get(baslangic + timedelta(days=offset), 0)),
            )
            for offset in range(90)
        ]
        miktarlar = [item.miktar for item in gecmis_seri]

        gunluk_tahmin = self._gunluk_tahmin_hesapla(miktarlar)
        tahmini_talep = round(max(0.0, gunluk_tahmin * tahmin_gun), 2)
        gunluk_ortalama_talep = round(max(0.0, gunluk_tahmin), 2)
        guvenli_stok = round(tahmini_talep + urun.min_stok, 2)
        onerilen_ikmal = round(max(0.0, guvenli_stok - urun.stok_miktari), 2)
        stok_riski = self._stok_riski_hesapla(
            mevcut_stok=urun.stok_miktari,
            min_stok=urun.min_stok,
            tahmini_talep=tahmini_talep,
        )

        return TalepTahminResponseDTO(
            urun=TalepTahminUrunOzetDTO(
                id=urun.id,
                isim=urun.isim,
                barkod=urun.barkod,
                min_stok=urun.min_stok,
                stok_miktari=urun.stok_miktari,
            ),
            tahmin_gun=tahmin_gun,
            gecmis_gunluk_seri=gecmis_seri,
            gelecek_gunluk_tahmin=[
                GunlukTahminDTO(
                    tarih=bitis + timedelta(days=offset),
                    tahmin=gunluk_ortalama_talep,
                )
                for offset in range(1, tahmin_gun + 1)
            ],
            tahmini_talep=tahmini_talep,
            gunluk_ortalama_talep=gunluk_ortalama_talep,
            guvenli_stok=guvenli_stok,
            onerilen_ikmal_miktari=onerilen_ikmal,
            stok_riski=stok_riski,
            talep_sinyali=self._talep_sinyali_hesapla(miktarlar, gunluk_tahmin),
            veri_guven_skoru=self._veri_guven_skoru_hesapla(miktarlar),
            trend=self._trend_hesapla(miktarlar),
            uyarilar=self._uyarilar_hazirla(miktarlar, stok_riski),
        )

    @staticmethod
    def _gunluk_tahmin_hesapla(miktarlar: list[float]) -> float:
        if not miktarlar or sum(miktarlar) <= 0:
            return 0.0

        son_7_ortalama = mean(miktarlar[-7:])
        son_30_ortalama = mean(miktarlar[-30:])
        gunluk_tahmin = (son_7_ortalama * 0.65) + (son_30_ortalama * 0.35)

        if len(miktarlar) >= 14:
            gunluk_tahmin *= TalepTahminiGetirUseCase._haftalik_trend_katsayisi(miktarlar)

        return gunluk_tahmin

    @staticmethod
    def _haftalik_trend_katsayisi(miktarlar: list[float]) -> float:
        onceki_hafta = miktarlar[-14:-7]
        son_hafta = miktarlar[-7:]
        onceki_ortalama = mean(onceki_hafta) if onceki_hafta else 0.0
        son_ortalama = mean(son_hafta) if son_hafta else 0.0

        if onceki_ortalama <= 0:
            return 1.0

        degisim_orani = (son_ortalama - onceki_ortalama) / onceki_ortalama
        sinirli_degisim = max(-0.25, min(0.25, degisim_orani))
        return 1.0 + (sinirli_degisim * 0.2)

    @staticmethod
    def _stok_riski_hesapla(
        mevcut_stok: float,
        min_stok: float,
        tahmini_talep: float,
    ) -> str:
        tahmin_sonrasi_stok = mevcut_stok - tahmini_talep
        if tahmin_sonrasi_stok <= 0:
            return "kritik"
        if tahmin_sonrasi_stok <= min_stok:
            return "dikkat"
        return "yok"

    @staticmethod
    def _talep_sinyali_hesapla(miktarlar: list[float], gunluk_tahmin: float) -> str:
        if gunluk_tahmin <= 0:
            return "dusuk"

        son_7_ortalama = mean(miktarlar[-7:])
        son_30_ortalama = mean(miktarlar[-30:])
        if son_30_ortalama <= 0:
            return "yuksek" if son_7_ortalama > 0 else "dusuk"

        oran = son_7_ortalama / son_30_ortalama
        if oran >= 1.2:
            return "yuksek"
        if oran <= 0.8:
            return "dusuk"
        return "normal"

    @staticmethod
    def _veri_guven_skoru_hesapla(miktarlar: list[float]) -> float:
        aktif_gun_sayisi = sum(1 for miktar in miktarlar if miktar > 0)
        if aktif_gun_sayisi == 0:
            return 0.0

        aktiflik_skoru = min(aktif_gun_sayisi / 30, 1.0)
        hacim_skoru = min(sum(miktarlar) / 100, 1.0)
        return round((aktiflik_skoru * 0.75) + (hacim_skoru * 0.25), 2)

    @staticmethod
    def _trend_hesapla(miktarlar: list[float]) -> TalepTrendDTO:
        onceki_ortalama = mean(miktarlar[-14:-7]) if len(miktarlar) >= 14 else 0.0
        son_ortalama = mean(miktarlar[-7:]) if len(miktarlar) >= 7 else 0.0

        if onceki_ortalama <= 0 and son_ortalama <= 0:
            return TalepTrendDTO(yon="stabil", degisim_orani=0.0, etiket="Stabil")
        if onceki_ortalama <= 0:
            return TalepTrendDTO(yon="pozitif", degisim_orani=1.0, etiket="Pozitif ivme")

        degisim_orani = (son_ortalama - onceki_ortalama) / onceki_ortalama
        if degisim_orani >= 0.05:
            return TalepTrendDTO(
                yon="pozitif",
                degisim_orani=round(degisim_orani, 4),
                etiket="Pozitif ivme",
            )
        if degisim_orani <= -0.05:
            return TalepTrendDTO(
                yon="negatif",
                degisim_orani=round(degisim_orani, 4),
                etiket="Negatif ivme",
            )
        return TalepTrendDTO(
            yon="stabil",
            degisim_orani=round(degisim_orani, 4),
            etiket="Stabil",
        )

    @staticmethod
    def _uyarilar_hazirla(miktarlar: list[float], stok_riski: str) -> list[str]:
        uyarilar: list[str] = []
        aktif_gun_sayisi = sum(1 for miktar in miktarlar if miktar > 0)

        if aktif_gun_sayisi == 0:
            uyarilar.append("Stok cikis gecmisi yok; cold-start tahmin dusuk guvenle uretildi.")
        elif aktif_gun_sayisi < 7:
            uyarilar.append("Aktif cikis gunu az; talep duzensiz veya yeni urun olabilir.")

        if stok_riski == "kritik":
            uyarilar.append("Tahmin ufkunda stok kritik seviyeye dusebilir.")
        elif stok_riski == "dikkat":
            uyarilar.append("Tahmin ufkunda stok minimum seviyeye yaklasabilir.")

        return uyarilar


from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean

from ml_models.talep_tahmin.domain.entities import (
    GunlukTahminNoktasi,
    InputFeatures,
    PredictionResult,
    TrendBilgisi,
)
from ml_models.talep_tahmin.domain.predictor import ITimeSeriesPredictor


class BaselineMovingAveragePredictor(ITimeSeriesPredictor):
    """Baseline demand predictor based on weighted moving averages.

    Sklearn'den bagimsiz, deterministik fallback. Faz 2'deki
    SklearnGradientBoostingPredictor'dan veri yetersizliginde dusulen
    guvenli baseline olarak da gorev yapar.
    """

    MODEL_VERSION = "baseline-ma-1.1"

    def __init__(
        self,
        recent_weight: float = 0.65,
        monthly_weight: float = 0.35,
        trend_weight: float = 0.2,
        belirsizlik_orani: float = 0.2,
    ) -> None:
        self._recent_weight = recent_weight
        self._monthly_weight = monthly_weight
        self._trend_weight = trend_weight
        self._belirsizlik_orani = belirsizlik_orani

    def predict(self, features: InputFeatures, tahmin_gun: int = 30) -> PredictionResult:
        miktarlar = [item.miktar for item in features.stok_cikis_gecmisi]
        gunluk_tahmin = self._gunluk_tahmin_hesapla(miktarlar, features)

        tahmini_talep = round(max(0.0, gunluk_tahmin * tahmin_gun), 2)
        gunluk_ortalama_talep = round(max(0.0, gunluk_tahmin), 2)
        guvenli_stok = round(tahmini_talep + features.min_stok, 2)
        onerilen_ikmal = round(max(0.0, guvenli_stok - features.mevcut_stok), 2)
        stok_riski = self._stok_riski_hesapla(
            mevcut_stok=features.mevcut_stok,
            min_stok=features.min_stok,
            tahmini_talep=tahmini_talep,
        )

        son_tarih = (
            features.stok_cikis_gecmisi[-1].tarih
            if features.stok_cikis_gecmisi
            else datetime.now(timezone.utc).date()
        )
        seri = self._gunluk_seri_uret(
            son_tarih=son_tarih,
            tahmin_gun=tahmin_gun,
            gunluk_tahmin=gunluk_ortalama_talep,
        )

        return PredictionResult(
            urun_id=features.urun_id,
            tahmin_gun=tahmin_gun,
            tahmini_talep=tahmini_talep,
            gunluk_ortalama_talep=gunluk_ortalama_talep,
            onerilen_ikmal_miktari=onerilen_ikmal,
            guvenli_stok=guvenli_stok,
            stok_riski=stok_riski,
            talep_sinyali=self._talep_sinyali_hesapla(miktarlar, gunluk_tahmin),
            veri_guven_skoru=self._veri_guven_skoru_hesapla(miktarlar),
            uyarilar=self._uyarilar_hazirla(miktarlar, stok_riski),
            gunluk_tahmin_serisi=seri,
            trend=self._trend_hesapla(miktarlar),
            model_versiyonu=self.MODEL_VERSION,
            son_hesaplanma=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

    def _gunluk_tahmin_hesapla(
        self,
        miktarlar: list[float],
        features: InputFeatures,
    ) -> float:
        if not miktarlar or sum(miktarlar) <= 0:
            return self._cold_start_tahmini(features)

        son_7 = miktarlar[-7:]
        son_30 = miktarlar[-30:]
        son_7_ortalama = mean(son_7) if son_7 else 0.0
        son_30_ortalama = mean(son_30) if son_30 else son_7_ortalama
        gunluk_tahmin = (
            son_7_ortalama * self._recent_weight
            + son_30_ortalama * self._monthly_weight
        )

        if len(miktarlar) >= 14:
            gunluk_tahmin *= self._haftalik_trend_katsayisi(miktarlar)

        return gunluk_tahmin

    @staticmethod
    def _cold_start_tahmini(features: InputFeatures) -> float:
        """Veri yokken kategori/marka medyanini fallback olarak kullan."""
        if features.kategori_ortalama_gunluk is not None:
            return float(features.kategori_ortalama_gunluk)
        if features.marka_ortalama_gunluk is not None:
            return float(features.marka_ortalama_gunluk)
        return 0.0

    def _haftalik_trend_katsayisi(self, miktarlar: list[float]) -> float:
        onceki_hafta = miktarlar[-14:-7]
        son_hafta = miktarlar[-7:]
        onceki_ortalama = mean(onceki_hafta) if onceki_hafta else 0.0
        son_ortalama = mean(son_hafta) if son_hafta else 0.0

        if onceki_ortalama <= 0:
            return 1.0

        degisim_orani = (son_ortalama - onceki_ortalama) / onceki_ortalama
        sinirli_degisim = max(-0.25, min(0.25, degisim_orani))
        return 1.0 + (sinirli_degisim * self._trend_weight)

    def _gunluk_seri_uret(
        self,
        son_tarih,
        tahmin_gun: int,
        gunluk_tahmin: float,
    ) -> list[GunlukTahminNoktasi]:
        seri: list[GunlukTahminNoktasi] = []
        alt = round(max(0.0, gunluk_tahmin * (1 - self._belirsizlik_orani)), 2)
        ust = round(max(gunluk_tahmin, gunluk_tahmin * (1 + self._belirsizlik_orani)), 2)
        for offset in range(1, tahmin_gun + 1):
            seri.append(
                GunlukTahminNoktasi(
                    tarih=son_tarih + timedelta(days=offset),
                    tahmin=gunluk_tahmin,
                    alt_sinir=alt,
                    ust_sinir=ust,
                )
            )
        return seri

    @staticmethod
    def _talep_sinyali_hesapla(miktarlar: list[float], gunluk_tahmin: float) -> str:
        if gunluk_tahmin <= 0:
            return "dusuk"
        if len(miktarlar) < 30:
            return "normal"

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
    def _trend_hesapla(miktarlar: list[float]) -> TrendBilgisi:
        onceki_ortalama = mean(miktarlar[-14:-7]) if len(miktarlar) >= 14 else 0.0
        son_ortalama = mean(miktarlar[-7:]) if len(miktarlar) >= 7 else 0.0

        if onceki_ortalama <= 0 and son_ortalama <= 0:
            return TrendBilgisi(yon="stabil", degisim_orani=0.0, etiket="Stabil")
        if onceki_ortalama <= 0:
            return TrendBilgisi(yon="pozitif", degisim_orani=1.0, etiket="Pozitif ivme")

        degisim_orani = (son_ortalama - onceki_ortalama) / onceki_ortalama
        if degisim_orani >= 0.05:
            return TrendBilgisi(
                yon="pozitif",
                degisim_orani=round(degisim_orani, 4),
                etiket="Pozitif ivme",
            )
        if degisim_orani <= -0.05:
            return TrendBilgisi(
                yon="negatif",
                degisim_orani=round(degisim_orani, 4),
                etiket="Negatif ivme",
            )
        return TrendBilgisi(
            yon="stabil",
            degisim_orani=round(degisim_orani, 4),
            etiket="Stabil",
        )

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
    def _veri_guven_skoru_hesapla(miktarlar: list[float]) -> float:
        if not miktarlar:
            return 0.0

        gun_skoru = min(len(miktarlar) / 90, 1.0)
        aktif_gun_sayisi = sum(1 for miktar in miktarlar if miktar > 0)
        aktiflik_skoru = min(aktif_gun_sayisi / 30, 1.0)
        return round((gun_skoru * 0.7) + (aktiflik_skoru * 0.3), 2)

    @staticmethod
    def _uyarilar_hazirla(miktarlar: list[float], stok_riski: str) -> list[str]:
        uyarilar: list[str] = []
        if not miktarlar:
            uyarilar.append("Stok cikis gecmisi yok; cold-start tahmin dusuk guvenle uretildi.")
        elif len(miktarlar) < 30:
            uyarilar.append("30 gunden az veri var; tahmin guveni sinirlidir.")

        aktif_gun_sayisi = sum(1 for miktar in miktarlar if miktar > 0)
        if miktarlar and aktif_gun_sayisi < 7:
            uyarilar.append("Aktif cikis gunu az; talep duzensiz veya yeni urun olabilir.")

        if stok_riski == "kritik":
            uyarilar.append("Tahmin ufkunda stok kritik seviyeye dusebilir.")
        elif stok_riski == "dikkat":
            uyarilar.append("Tahmin ufkunda stok minimum seviyeye yaklasabilir.")

        return uyarilar

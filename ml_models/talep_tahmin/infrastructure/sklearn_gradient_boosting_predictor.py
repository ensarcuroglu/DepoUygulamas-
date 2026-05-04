"""scikit-learn GradientBoostingRegressor tabanli talep tahmini.

Tek bir urun icin ekleme talep serisinden 3 ayri quantile model egitir:
- q10 (alt sinir, %10 kantil)
- q50 (medyan / nokta tahmini)
- q90 (ust sinir, %90 kantil)

Multi-step forecast recursive yapilir: her gun tahmini once gecmis seriye
eklenir, ardindan bir sonraki gunun feature'lari yeniden hesaplanir.

Veri yetersiz oldugunda BaselineMovingAveragePredictor'a fallback eder.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Optional

from ml_models.talep_tahmin.domain.entities import (
    GunlukTahminNoktasi,
    InputFeatures,
    PredictionResult,
    TrendBilgisi,
)
from ml_models.talep_tahmin.domain.predictor import ITimeSeriesPredictor
from ml_models.talep_tahmin.infrastructure.baseline_moving_average_predictor import (
    BaselineMovingAveragePredictor,
)
from ml_models.talep_tahmin.infrastructure.feature_builders import (
    TimeSeriesFeatureBuilder,
    gunluk_seriyi_densify,
)

logger = logging.getLogger(__name__)

_FEATURE_KOLONLARI = (
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_30",
    "rolling_mean_7",
    "rolling_mean_30",
    "rolling_std_7",
    "dow",
    "is_weekend",
    "month",
    "is_holiday",
    "kategori_id",
    "marka_id",
)


class SklearnGradientBoostingPredictor(ITimeSeriesPredictor):
    """Quantile loss + GradientBoostingRegressor (recursive multi-step)."""

    MODEL_VERSION = "sklearn-gbr-quantile-1.0"
    MIN_TRAINING_GUN = 30  # bunun altinda baseline'a fallback

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 3,
        learning_rate: float = 0.05,
        random_state: int = 42,
        baseline_fallback: Optional[BaselineMovingAveragePredictor] = None,
    ) -> None:
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._learning_rate = learning_rate
        self._random_state = random_state
        self._builder = TimeSeriesFeatureBuilder()
        self._baseline = baseline_fallback or BaselineMovingAveragePredictor()

    def predict(self, features: InputFeatures, tahmin_gun: int = 30) -> PredictionResult:
        gunluk_seri = [
            (item.tarih, float(item.miktar)) for item in features.stok_cikis_gecmisi
        ]
        if len(gunluk_seri) < self.MIN_TRAINING_GUN:
            sonuc = self._baseline.predict(features, tahmin_gun=tahmin_gun)
            return _baseline_sonucunu_isaretle(
                sonuc,
                neden="Yetersiz egitim verisi: baseline'a fallback edildi.",
            )

        # Eksik gunleri 0 ile doldur — sklearn icin yogun seri sart
        densified = gunluk_seriyi_densify(gunluk_seri)

        try:
            q10_model, q50_model, q90_model = self._modelleri_egit(
                densified=densified,
                features=features,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Sklearn predictor egitim hatasi (%s); baseline fallback", exc)
            sonuc = self._baseline.predict(features, tahmin_gun=tahmin_gun)
            return _baseline_sonucunu_isaretle(
                sonuc,
                neden=f"Sklearn egitim hatasi: {exc!s}; baseline fallback.",
            )

        son_tarih = densified[-1][0]
        gecmis_sayilar = [value for _, value in densified]
        tatil_gunleri = set(features.tatil_gunleri)

        seri: list[GunlukTahminNoktasi] = []
        nokta_tahminler: list[float] = []
        for offset in range(1, tahmin_gun + 1):
            gun_tarihi = son_tarih + timedelta(days=offset)
            satir = self._builder.build_inference_row(
                tarih=gun_tarihi,
                gecmis=gecmis_sayilar,
                tatil_gunleri=tatil_gunleri,
                kategori_id=features.kategori_id or 0,
                marka_id=features.marka_id or 0,
            )
            x = _satiri_vektore_cevir(satir)
            q10 = max(0.0, float(q10_model.predict([x])[0]))
            q50 = max(0.0, float(q50_model.predict([x])[0]))
            q90 = max(q50, float(q90_model.predict([x])[0]))
            seri.append(
                GunlukTahminNoktasi(
                    tarih=gun_tarihi,
                    tahmin=round(q50, 2),
                    alt_sinir=round(min(q10, q50), 2),
                    ust_sinir=round(q90, 2),
                )
            )
            nokta_tahminler.append(q50)
            gecmis_sayilar = gecmis_sayilar + [q50]

        tahmini_talep = round(sum(nokta_tahminler), 2)
        gunluk_ortalama = round(mean(nokta_tahminler), 2) if nokta_tahminler else 0.0
        guvenli_stok = round(tahmini_talep + features.min_stok, 2)
        onerilen_ikmal = round(max(0.0, guvenli_stok - features.mevcut_stok), 2)
        stok_riski = _stok_riski_hesapla(
            mevcut_stok=features.mevcut_stok,
            min_stok=features.min_stok,
            tahmini_talep=tahmini_talep,
        )
        miktarlar = [value for _, value in densified]

        return PredictionResult(
            urun_id=features.urun_id,
            tahmin_gun=tahmin_gun,
            tahmini_talep=tahmini_talep,
            gunluk_ortalama_talep=gunluk_ortalama,
            onerilen_ikmal_miktari=onerilen_ikmal,
            guvenli_stok=guvenli_stok,
            stok_riski=stok_riski,
            talep_sinyali=_talep_sinyali_hesapla(miktarlar, gunluk_ortalama),
            veri_guven_skoru=_veri_guven_skoru(miktarlar),
            uyarilar=_uyarilar(miktarlar, stok_riski),
            gunluk_tahmin_serisi=seri,
            trend=_trend_hesapla(miktarlar),
            model_versiyonu=self.MODEL_VERSION,
            son_hesaplanma=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

    def _modelleri_egit(self, densified, features: InputFeatures):
        """Q10/Q50/Q90 modellerini egit ve geri don."""
        from sklearn.ensemble import GradientBoostingRegressor

        rows = self._builder.build_training_matrix(
            gunluk_seri=densified,
            tatil_gunleri=set(features.tatil_gunleri),
            kategori_id=features.kategori_id or 0,
            marka_id=features.marka_id or 0,
        )
        if len(rows) < self.MIN_TRAINING_GUN // 2:
            raise ValueError(
                f"Egitim icin yeterli pencere yok: {len(rows)} satir."
            )

        x_matrix = [_satiri_vektore_cevir(r) for r in rows]
        y_target = [r.target for r in rows]

        def _gbr(alpha: float) -> "GradientBoostingRegressor":
            return GradientBoostingRegressor(
                loss="quantile",
                alpha=alpha,
                n_estimators=self._n_estimators,
                max_depth=self._max_depth,
                learning_rate=self._learning_rate,
                random_state=self._random_state,
            )

        q10 = _gbr(0.1).fit(x_matrix, y_target)
        q50 = _gbr(0.5).fit(x_matrix, y_target)
        q90 = _gbr(0.9).fit(x_matrix, y_target)
        return q10, q50, q90


def _satiri_vektore_cevir(row) -> list[float]:
    return [float(getattr(row, kolon)) for kolon in _FEATURE_KOLONLARI]


def _baseline_sonucunu_isaretle(sonuc: PredictionResult, neden: str) -> PredictionResult:
    """Baseline'dan donen PredictionResult'u sklearn predictor agzindan isaretle."""
    yeni_uyarilar = list(sonuc.uyarilar) + [neden]
    return sonuc.model_copy(
        update={
            "uyarilar": yeni_uyarilar,
            "model_versiyonu": f"{sonuc.model_versiyonu}+sklearn-fallback",
        }
    )


def _stok_riski_hesapla(mevcut_stok: float, min_stok: float, tahmini_talep: float) -> str:
    tahmin_sonrasi = mevcut_stok - tahmini_talep
    if tahmin_sonrasi <= 0:
        return "kritik"
    if tahmin_sonrasi <= min_stok:
        return "dikkat"
    return "yok"


def _talep_sinyali_hesapla(miktarlar: list[float], gunluk_tahmin: float) -> str:
    if gunluk_tahmin <= 0:
        return "dusuk"
    if len(miktarlar) < 30:
        return "normal"
    son_7 = mean(miktarlar[-7:])
    son_30 = mean(miktarlar[-30:])
    if son_30 <= 0:
        return "yuksek" if son_7 > 0 else "dusuk"
    oran = son_7 / son_30
    if oran >= 1.2:
        return "yuksek"
    if oran <= 0.8:
        return "dusuk"
    return "normal"


def _veri_guven_skoru(miktarlar: list[float]) -> float:
    if not miktarlar:
        return 0.0
    gun_skoru = min(len(miktarlar) / 90, 1.0)
    aktif = sum(1 for m in miktarlar if m > 0)
    aktiflik = min(aktif / 30, 1.0)
    return round((gun_skoru * 0.6) + (aktiflik * 0.4), 2)


def _trend_hesapla(miktarlar: list[float]) -> TrendBilgisi:
    if len(miktarlar) < 14:
        return TrendBilgisi(yon="stabil", degisim_orani=0.0, etiket="Stabil")
    onceki = mean(miktarlar[-14:-7])
    son = mean(miktarlar[-7:])
    if onceki <= 0 and son <= 0:
        return TrendBilgisi(yon="stabil", degisim_orani=0.0, etiket="Stabil")
    if onceki <= 0:
        return TrendBilgisi(yon="pozitif", degisim_orani=1.0, etiket="Pozitif ivme")
    degisim = (son - onceki) / onceki
    if degisim >= 0.05:
        return TrendBilgisi(yon="pozitif", degisim_orani=round(degisim, 4), etiket="Pozitif ivme")
    if degisim <= -0.05:
        return TrendBilgisi(yon="negatif", degisim_orani=round(degisim, 4), etiket="Negatif ivme")
    return TrendBilgisi(yon="stabil", degisim_orani=round(degisim, 4), etiket="Stabil")


def _uyarilar(miktarlar: list[float], stok_riski: str) -> list[str]:
    uyarilar: list[str] = []
    if not miktarlar:
        uyarilar.append("Stok cikis gecmisi yok; cold-start tahmin dusuk guvenle uretildi.")
    elif len(miktarlar) < 30:
        uyarilar.append("30 gunden az veri var; tahmin guveni sinirlidir.")

    aktif = sum(1 for m in miktarlar if m > 0)
    if miktarlar and aktif < 7:
        uyarilar.append("Aktif cikis gunu az; talep duzensiz veya yeni urun olabilir.")

    if stok_riski == "kritik":
        uyarilar.append("Tahmin ufkunda stok kritik seviyeye dusebilir.")
    elif stok_riski == "dikkat":
        uyarilar.append("Tahmin ufkunda stok minimum seviyeye yaklasabilir.")

    return uyarilar

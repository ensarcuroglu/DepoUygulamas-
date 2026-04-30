from __future__ import annotations

from datetime import date, timedelta
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
from ml_models.talep_tahmin.application import PredictDemandUseCase
from ml_models.talep_tahmin.domain import (
    DailyStockExit,
    InputFeatures,
    PredictionResult,
)
from ml_models.talep_tahmin.infrastructure.feature_builders import (
    tatil_aralik_listesi,
)


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
            _urun_kaydi_to_ozet(urun)
            for urun in self._repo.urunleri_listele(limit=limit, search=search)
        ]


class TalepTahminiGetirUseCase:
    """Predictor'a delege eden ince orkestrasyon katmani.

    Algoritma `ml_models.talep_tahmin` paketinde; bu sinif sadece I/O
    adaptasyonu yapar (repo'dan veriyi cek, predictor'a gonder, DTO'ya
    cevir).
    """

    GECMIS_PENCERE_GUN = 90

    def __init__(
        self,
        repo: ITalepTahminiRepository,
        predict_uc: PredictDemandUseCase,
    ):
        self._repo = repo
        self._predict_uc = predict_uc

    def execute(self, urun_id: int, tahmin_gun: int = 7) -> TalepTahminResponseDTO:
        urun = self._repo.urun_getir(urun_id)
        if urun is None:
            raise KayitBulunamadiError("Urun", urun_id)

        bitis = date.today()
        baslangic = bitis - timedelta(days=self.GECMIS_PENCERE_GUN - 1)
        gunluk_cikislar = self._repo.gunluk_cikislari_getir(urun_id, baslangic, bitis)
        cikis_by_date = {item.tarih: item.miktar for item in gunluk_cikislar}

        gecmis_seri = [
            GunlukTalepDTO(
                tarih=baslangic + timedelta(days=offset),
                miktar=float(cikis_by_date.get(baslangic + timedelta(days=offset), 0)),
            )
            for offset in range(self.GECMIS_PENCERE_GUN)
        ]

        # Tatil gunleri: gecmis pencere + tahmin ufku
        tatil_gunleri = tatil_aralik_listesi(
            baslangic,
            bitis + timedelta(days=tahmin_gun),
        )

        # Kategori/marka cold-start fallback medyani
        kategori_medyan: Optional[float] = None
        marka_medyan: Optional[float] = None
        if urun.kategori_id is not None:
            kategori_medyan = self._repo.kategori_gunluk_medyan(urun.kategori_id)
        if urun.marka_id is not None:
            marka_medyan = self._repo.marka_gunluk_medyan(urun.marka_id)

        features = InputFeatures(
            urun_id=urun.id,
            stok_cikis_gecmisi=[
                DailyStockExit(tarih=item.tarih, miktar=item.miktar)
                for item in gecmis_seri
                if item.miktar > 0
            ],
            mevcut_stok=float(urun.stok_miktari),
            min_stok=float(urun.min_stok),
            kategori_id=urun.kategori_id,
            marka_id=urun.marka_id,
            tatil_gunleri=tatil_gunleri,
            kategori_ortalama_gunluk=kategori_medyan,
            marka_ortalama_gunluk=marka_medyan,
        )
        sonuc: PredictionResult = self._predict_uc.execute(features, tahmin_gun=tahmin_gun)

        gelecek_seri = [
            GunlukTahminDTO(
                tarih=nokta.tarih,
                tahmin=nokta.tahmin,
                alt_sinir=nokta.alt_sinir,
                ust_sinir=nokta.ust_sinir,
            )
            for nokta in sonuc.gunluk_tahmin_serisi
        ]
        if not gelecek_seri:
            # Predictor seri uretemediyse (cold-start vb.) flat fallback
            gelecek_seri = [
                GunlukTahminDTO(
                    tarih=bitis + timedelta(days=offset),
                    tahmin=sonuc.gunluk_ortalama_talep,
                    alt_sinir=sonuc.gunluk_ortalama_talep,
                    ust_sinir=sonuc.gunluk_ortalama_talep,
                )
                for offset in range(1, tahmin_gun + 1)
            ]

        trend = sonuc.trend or _stabil_trend()

        return TalepTahminResponseDTO(
            urun=_urun_kaydi_to_ozet(urun),
            tahmin_gun=tahmin_gun,
            gecmis_gunluk_seri=gecmis_seri,
            gelecek_gunluk_tahmin=gelecek_seri,
            tahmini_talep=sonuc.tahmini_talep,
            gunluk_ortalama_talep=sonuc.gunluk_ortalama_talep,
            guvenli_stok=sonuc.guvenli_stok,
            onerilen_ikmal_miktari=sonuc.onerilen_ikmal_miktari,
            stok_riski=sonuc.stok_riski,
            talep_sinyali=sonuc.talep_sinyali,
            veri_guven_skoru=sonuc.veri_guven_skoru,
            trend=TalepTrendDTO(
                yon=trend.yon,
                degisim_orani=trend.degisim_orani,
                etiket=trend.etiket,
            ),
            uyarilar=sonuc.uyarilar,
            model_versiyonu=sonuc.model_versiyonu,
            son_hesaplanma=sonuc.son_hesaplanma,
        )


def _urun_kaydi_to_ozet(urun) -> TalepTahminUrunOzetDTO:
    return TalepTahminUrunOzetDTO(
        id=urun.id,
        isim=urun.isim,
        barkod=urun.barkod,
        min_stok=urun.min_stok,
        stok_miktari=urun.stok_miktari,
        kategori_id=getattr(urun, "kategori_id", None),
        marka_id=getattr(urun, "marka_id", None),
    )


def _stabil_trend() -> TalepTrendDTO:
    return TalepTrendDTO(yon="stabil", degisim_orani=0.0, etiket="Stabil")

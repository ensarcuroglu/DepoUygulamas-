from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from app.application.dto.talep_tahmini_dto import (
    BacktestOzetDTO,
    GunlukTahminDTO,
    GunlukTalepDTO,
    RiskliUrunDTO,
    TalepTahminResponseDTO,
    TalepTahminUrunOzetDTO,
    TalepTrendDTO,
)
from app.core.exceptions import KayitBulunamadiError
from app.core.repositories.talep_tahmini_repository import (
    CacheKaydi,
    ITalepTahminCacheRepository,
    ITalepTahminiRepository,
)
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
        cache_repo: Optional[ITalepTahminCacheRepository] = None,
    ):
        self._repo = repo
        self._predict_uc = predict_uc
        self._cache_repo = cache_repo

    def execute(
        self,
        urun_id: int,
        tahmin_gun: int = 7,
        force_recompute: bool = False,
    ) -> TalepTahminResponseDTO:
        # Cache check — gun ici tekrar hesaplamayi engeller (nightly job sabah 02:00)
        if self._cache_repo is not None and not force_recompute:
            cached = self._cache_repo.getir(urun_id, tahmin_gun)
            if cached and cached.hesaplanma_tarihi == date.today():
                response = self._payload_to_response(cached.payload)
                if response is not None:
                    return response

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

        response = TalepTahminResponseDTO(
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

        # Write-through: gun ici tekrar hesaplamayi engellemek icin cache'e yaz
        if self._cache_repo is not None:
            try:
                self._cache_repo.yaz(
                    CacheKaydi(
                        urun_id=urun.id,
                        tahmin_gun=tahmin_gun,
                        payload=response.model_dump(mode="json"),
                        stok_riski=response.stok_riski,
                        tahmini_talep=float(response.tahmini_talep),
                        onerilen_ikmal=float(response.onerilen_ikmal_miktari),
                        veri_guven_skoru=float(response.veri_guven_skoru),
                        model_versiyonu=response.model_versiyonu or "unknown",
                        hesaplanma_tarihi=date.today(),
                    )
                )
            except Exception:  # cache hatasi response'u bozmamali
                pass

        return response

    @staticmethod
    def _payload_to_response(payload: dict) -> Optional[TalepTahminResponseDTO]:
        try:
            return TalepTahminResponseDTO.model_validate(payload)
        except Exception:
            return None


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


class RiskliUrunlerListeleUseCase:
    """Cache'ten kritik/dikkat seviyeli urunleri toplu sunar.

    Cache miss (nightly job henuz calismamis) durumunda bos liste doner;
    on-demand toplu hesap yapilmaz — runtime'i korumak icin.
    """

    def __init__(
        self,
        repo: ITalepTahminiRepository,
        cache_repo: ITalepTahminCacheRepository,
    ):
        self._repo = repo
        self._cache_repo = cache_repo

    def execute(
        self,
        tahmin_gun: int = 7,
        risk_seviyeleri: tuple[str, ...] = ("kritik", "dikkat"),
        limit: int = 50,
    ) -> list[RiskliUrunDTO]:
        kayitlar = self._cache_repo.riskli_urunler(
            tahmin_gun=tahmin_gun,
            risk_seviyeleri=risk_seviyeleri,
            limit=limit,
        )
        sonuc: list[RiskliUrunDTO] = []
        for kayit in kayitlar:
            urun = self._repo.urun_getir(kayit.urun_id)
            if urun is None:
                continue
            payload = kayit.payload or {}
            sonuc.append(
                RiskliUrunDTO(
                    urun=_urun_kaydi_to_ozet(urun),
                    tahmin_gun=kayit.tahmin_gun,
                    tahmini_talep=kayit.tahmini_talep,
                    gunluk_ortalama_talep=float(
                        payload.get("gunluk_ortalama_talep", 0.0)
                    ),
                    onerilen_ikmal_miktari=kayit.onerilen_ikmal,
                    stok_riski=kayit.stok_riski,
                    talep_sinyali=str(payload.get("talep_sinyali", "normal")),
                    veri_guven_skoru=kayit.veri_guven_skoru,
                    son_hesaplanma=str(payload.get("son_hesaplanma"))
                    if payload.get("son_hesaplanma") is not None
                    else None,
                )
            )
        return sonuc


class BacktestOzetGetirUseCase:
    """Modelin son N gun icindeki accuracy ozetini hesaplar.

    Yontem: tahmin pencereyi T gun once ayarla, son T gun gercek cikislari
    actual olarak al; pencere oncesi (T*2..T) ortalamasini "naive forecast"
    olarak al, MAE / MAPE hesapla. Hizli ve veri gerektirmeyen bir baseline
    accuracy gostergesidir.
    """

    PENCERE_GUN = 30
    URUN_LIMIT = 50

    def __init__(
        self,
        repo: ITalepTahminiRepository,
        predict_uc: PredictDemandUseCase,
    ):
        self._repo = repo
        self._predict_uc = predict_uc

    def execute(self, tahmin_gun: int = 7) -> BacktestOzetDTO:
        bitis = date.today()
        baslangic = bitis - timedelta(days=self.PENCERE_GUN * 2)

        urun_idleri = self._repo.aktif_urun_idleri()[: self.URUN_LIMIT]
        mae_toplam = 0.0
        mape_toplam = 0.0
        sayilan = 0

        for urun_id in urun_idleri:
            cikislar = self._repo.gunluk_cikislari_getir(
                urun_id, baslangic, bitis
            )
            if len(cikislar) < self.PENCERE_GUN:
                continue
            miktarlar = [c.miktar for c in cikislar]
            actual_pencere = miktarlar[-self.PENCERE_GUN :]
            tahmin_pencere = miktarlar[
                -self.PENCERE_GUN * 2 : -self.PENCERE_GUN
            ]
            if not actual_pencere or not tahmin_pencere:
                continue
            tahmin = sum(tahmin_pencere) / len(tahmin_pencere)
            actual_ort = sum(actual_pencere) / len(actual_pencere)

            mae_toplam += abs(actual_ort - tahmin)
            payda = max(actual_ort, 1.0)
            mape_toplam += abs(actual_ort - tahmin) / payda
            sayilan += 1

        if sayilan == 0:
            return BacktestOzetDTO(
                tahmin_gun=tahmin_gun,
                mae=0.0,
                mape=0.0,
                urun_sayisi=0,
                model_versiyonu=getattr(
                    self._predict_uc._predictor, "MODEL_VERSION", "baseline"
                ),
            )

        return BacktestOzetDTO(
            tahmin_gun=tahmin_gun,
            mae=round(mae_toplam / sayilan, 3),
            mape=round((mape_toplam / sayilan) * 100, 2),
            urun_sayisi=sayilan,
            model_versiyonu=getattr(
                self._predict_uc._predictor, "MODEL_VERSION", "baseline"
            ),
        )

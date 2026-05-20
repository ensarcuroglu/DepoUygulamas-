# Talep Tahmin Model Alani

Bu alan, urun bazli talep tahmini icin bagimsiz model gelistirme ve dogrulama calismalarini barindirir.
Proje SaaS/B2B urun olarak gelistirildigi icin musteri verisi yokken sentetik veri
ve acik kaynak veri adapterleriyle demo/backtest yapilabilir.

## Hedef

Mevcut projedeki gercek veri kaynaklarindan turetilen gunluk urun cikis/talep serileriyle:

- 7/30/90 gunluk tahmini talep,
- stok riski,
- onerilen ikmal miktari,
- veri yeterliligi ve guven skoru

uretebilen sade ve gelistirilebilir bir tahmin altyapisi hazirlamak.

Musteri verisi olmayan asamada hedef, model dogrulugunu kesin iddia etmek degil;
veri sozlesmesini, entegrasyon sinirlarini, cold-start davranisini ve demo
deneyimini guvenilir hale getirmektir.

## Clean Architecture Katmanlari

- `domain/`: Tahmin problemine ait saf is kurallari ve hesaplama kavramlari.
- `application/`: Use-case, port ve DTO sozlesmeleri.
- `infrastructure/`: CSV/DB veri okuyucu, feature hazirlama, model kayit ve adaptorleri.
- `interfaces/`: CLI, notebook veya ileride API adaptorleri gibi dis arayuzler.
- `experiments/`: Deneysel model denemeleri; uretim kodu sayilmaz.
- `tests/`: Model hesaplama ve veri sozlesmesi testleri.

## Uretim Entegrasyonu

Bu paket **uretim akisinda dogrudan kullaniliyor**. BackendProje, `ml_models.talep_tahmin` paketini su uc noktada ithal eder:

- `BackendProje/app/application/use_cases/talep_tahmini_use_cases.py` — `PredictDemandUseCase`, `InputFeatures`, `DailyStockExit`, `PredictionResult` ve `tatil_aralik_listesi` kullanir.
- `BackendProje/app/infrastructure/di/modules/talep_tahmini_di.py` — `ITimeSeriesPredictor`, `SklearnGradientBoostingPredictor`, `BaselineMovingAveragePredictor` singleton'larini kurar. Sklearn yukluyse gradient boosting aktif olur; yoksa baseline'a fallback eder.
- API zinciri: `GET /api/talep-tahmini/urunler/{urun_id}` -> `TalepTahminiGetirUseCase` -> `PredictDemandUseCase` -> aktif `ITimeSeriesPredictor`.

Backend katmani sadece I/O adaptasyonu (MySQL'den 90 gunluk cikis serisi -> `InputFeatures`, `PredictionResult` -> `TalepTahminResponseDTO`) ve `talep_tahmin_cache` write-through cache'ini yonetir. Algoritma ve karar logic'i bu pakette kalir.

### Aktif Predictor

- `SklearnGradientBoostingPredictor`: lag/rolling/calendar feature'lariyla q10/q50/q90 quantile modeli; recursive multi-step forecast. Veri yetersizliginde icinde `BaselineMovingAveragePredictor`'a duser.
- `BaselineMovingAveragePredictor`: sklearn yokken veya cold-start durumunda kullanilan referans model.

### Veri Kaynaklari

- Uretim: `ITalepTahminiRepository` (MySQL) — gercek stok hareketleri.
- Offline backtest / demo:
  - `SyntheticDemandDataSource` — deterministik sentetik profiller (`experiments/run_demo_backtest.py`).
  - `ParquetDemandDataSource` — DataGenService `timeseries_history` parquet ciktisini canonical `InputFeatures`'a cevirir (`experiments/backtest_datagen_parquet.py`).
  - `CsvDemandDataSource`, `PublicDatasetAdapter` — kanonik CSV / acik veri kaynaklari.

Bu data source'lar yalniz `experiments/` ve test akislarinda kullanilir; uretim isteklerine baglanmaz.

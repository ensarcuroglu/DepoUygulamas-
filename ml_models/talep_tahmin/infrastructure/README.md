# Infrastructure

Veri okuma, feature hazirlama ve model kayit adaptorleri bu katmandadir.

Bu katman:

- CSV veya snapshot veri okur,
- ileride SQLAlchemy veya backend repository adaptorlerine baglanabilir,
- model artefact kayit/yukleme islerini barindirir.

Alt klasorler:

- `data_sources/`: CSV, JSON veya DB veri kaynaklari.
- `feature_builders/`: Gunluk urun serisi ve model input hazirlama.
- `model_registry/`: Egitilmis model dosyalarini yukleme/kaydetme adaptorleri.
- `repositories/`: Veri erisim implementasyonlari.

# ML Models

Bu klasor, Depo Yonetim Sistemi icin backend akisini bozmadan ML/AI modellerini gelistirmek ve test etmek icin ayrilmis calisma alanidir.

Ana ilke: Model denemeleri burada yapilir; FastAPI backend'e yalnizca test edilmis, input/output sozlesmesi netlesmis servisler baglanir.

## Yapi

- `talep_tahmin/`: Urun bazli talep tahmini modeli ve deneyleri.

## Kurallar

- Backend tablolari veya API endpointleri burada dogrudan degistirilmez.
- Ham veri, islenmis veri, model artefact'leri ve rapor ciktilari Git'e eklenmez.
- Uretime alinacak mantik once `domain`, `application`, `infrastructure`, `interfaces` ayrimina gore netlestirilir.
- Backend entegrasyonu yapilirken mevcut `app/application`, `app/core`, `app/infrastructure` mimarisiyle ayni sozluk ve DTO yaklasimi korunur.

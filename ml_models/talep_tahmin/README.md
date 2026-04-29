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

## Uretim Entegrasyon Notu

Bu klasordeki calisma dogrudan backend akisini degistirmez. Backend entegrasyonu sirasinda onerilen cikti, `TalepTahminServisi` gibi bir servisle FastAPI tarafina tasinmalidir.

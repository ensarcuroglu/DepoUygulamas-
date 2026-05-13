---
id: fefo-sureci
audience: operator
aliases:
  - FEFO
  - First Expired First Out
  - son kullanma onceligi
  - SKT onceligi
  - SKT siralamasi
related:
  - glossary
  - toplama-pick-sureci
  - sevkiyat-sureci
updated: 2026-05-13
verified: true
---

# FEFO Sureci

## Amac

FEFO, son kullanma tarihi en yakin olan uygun stoklarin once kullanilmasini veya sevk edilmesini saglayan stok yonetimi kuralidir. Amac, son kullanma tarihi yaklasan urunlerin depoda bekleyerek fireye donusmesini azaltmak ve sevkiyat sirasini kontrollu hale getirmektir.

Kullanici FEFO mantigi, SKT onceligi, lot secimi veya sevkiyat sirasini sordugunda asistan bu dokumandaki kurallara gore cevap vermelidir.

## Kapsam

- Kapsama giren isler:
  - SKT bilgisi olan urunlerde stok secim onceligi.
  - Lot veya parti bazli urunlerde sevkiyat onerisi.
  - Toplama, sevkiyat ve cikis planlama sirasinda uygun stok belirleme.
  - Ayni urunden birden fazla SKT veya lot bulundugunda onceliklendirme.

- Kapsam disi isler:
  - SKT bilgisi olmayan urunlerde FEFO yerine farkli stok cikis kurallari uygulanabilir.
  - Blokeli, hasarli, kalite kontrol bekleyen veya sevke kapali stoklar FEFO onerisine dahil edilmez.
  - Musteriye ozel sozlesme, kampanya veya manuel operasyon kararlari bu dokumanin disindadir.

## Temel Kurallar

- FEFO acilimi First Expired, First Out seklindedir.
- Sistem, ayni urun icin son kullanma tarihi en yakin olan uygun stogu once onerir.
- Son kullanma tarihi gecmis stoklar normal sevkiyat icin uygun kabul edilmez.
- Blokeli, hasarli, rezerve edilmis veya kalite kontrol bekleyen stoklar secim disinda tutulur.
- Ayni SKT tarihine sahip birden fazla stok varsa sistem lot, lokasyon, miktar veya operasyonel uygunluk gibi ek kriterlerle siralama yapabilir.
- FEFO, FIFO ile ayni sey degildir. FIFO ilk giren stogu once cikarir; FEFO son kullanma tarihi en yakin stogu once cikarir.
- Manuel kullanici mudahalesi varsa operasyon sorumlusu gerekceyi kontrol etmelidir (toplama gorevinde `fefo_override` bayragi ile isaretlenir).

## Adimlar

1. Kullanici veya sistem bir urun icin cikis, toplama ya da sevkiyat ihtiyaci olusturur.
2. Sistem ilgili urunun uygun stoklarini listeler.
3. Blokeli, hasarli, kalite kontrol bekleyen, sevke kapali veya uygun olmayan stoklar elenir.
4. Kalan stoklar son kullanma tarihine gore en yakindan en uzaga siralanir.
5. Ihtiyac miktari, en yakin SKT tarihli uygun stoktan baslanarak karsilanir.
6. Yeterli miktar tek stoktan karsilanamazsa sistem sonraki en yakin SKT tarihli uygun stoga gecer.
7. Toplama veya sevkiyat emri bu oncelik sirasina gore olusturulur.

## Istisnalar

- Urunun SKT bilgisi yoksa asistan FEFO karari icin yeterli bilgi olmadigini soylemelidir.
- Dokumanda urune ozel bir istisna yoksa asistan urune ozel kesin kural uydurmamalidir.
- Stok blokeli, hasarli, kalite kontrol bekliyor veya sevke kapaliysa SKT tarihi yakin olsa bile onerilmez.
- Musteri ozel talimatlari varsa bu talimatlar operasyon sorumlusu tarafindan ayrica kontrol edilmelidir.
- FEFO ile sistemde gorunen stok onerisi celisiyorsa kullanici stok durumu, blokaj, rezervasyon ve SKT alanlarini kontrol etmelidir.

## Ornek Sorular

- FEFO mantigi nedir?
- FEFO nasil calisir?
- SKT tarihi en yakin olan urun neden once oneriliyor?
- FEFO ile FIFO arasindaki fark nedir?
- Blokeli stok FEFO sirasina girer mi?
- Son kullanma tarihi gecmis urun sevk edilir mi?
- Ayni SKT tarihindeki lotlar nasil siralanir?
- Sistem neden daha eski girisli stogu degil de SKT tarihi yakin stogu onerdi?

## Kisa Cevap Ozeti

FEFO, son kullanma tarihi en yakin uygun stokun once kullanilmasi veya sevk edilmesi kuralidir. Sistem once sevke uygun stoklari belirler, blokeli veya uygun olmayan stoklari eler ve kalanlari SKT tarihine gore siralar. FEFO, FIFO'dan farklidir; FIFO giris tarihine, FEFO ise son kullanma tarihine bakar.

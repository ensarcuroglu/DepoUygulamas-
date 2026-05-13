---
id: toplama-pick-sureci
audience: operator
aliases:
  - toplama
  - picking
  - pick
  - sevk hazirligi
  - palet toplama
  - urun toplama
related:
  - glossary
  - fefo-sureci
  - sevkiyat-sureci
  - sistem-genel-bakis
updated: 2026-05-13
verified: false
---

# Toplama (Pick) Sureci

## Amac

Toplama, siparis veya sevkiyat icin gerekli urunlerin paletlerden raftan toplanmasi surecidir. Sistem siparis kalemleri ve FEFO oncelige gore toplama gorevleri olusturur. Operator gorevi havuzdan ceker, paleti raftan alir ve toplama alanina/yukleme kapisina goturur.

Kullanici "toplama nasil yapilir", "pick gorevi", "FEFO override", "tam koli", "palet sevk hazirligi" sorulari sordugunda asistan bu dokumana basvurmalidir.

## Kapsam

- Kapsama giren isler:
  - Bir sevkiyata bagli toplama gorevlerinin olusumu ve akisi.
  - FEFO sirasi ile palet onerisi.
  - Operatorun FEFO disinda farkli palet secmesi (`fefo_override`).
  - Gorev iptal/tamamla durumlari.
- Kapsam disi isler:
  - Sevkiyat plani ve cikis stok hareketi (sevkiyat-sureci dokumaninda).
  - FEFO algoritmasinin detayli kurallari (fefo-sureci dokumaninda).
  - Yukleme kapisinda fiziksel kontrol.

## Temel Kurallar

- Toplama gorevi durum makinesi: **Beklemede** → **Atandi** → **DevamEdiyor** → **Tamamlandi**. Iptal her aktif durumdan mumkundur.
- Pull-based atama: Operator havuzdan kendisi ceker. `Atandi` durumu kilitlidir.
- `Atandi` durumundan operator gorevi `Beklemede`'ye birakabilir; atama bilgisi temizlenir.
- Sistem palet onerisini **FEFO** mantigi ile yapar: ayni urun icin SKT'si en yakin uygun palet once onerilir.
- Operator FEFO onerisi disinda farkli bir palet alirsa `fefo_override=True` isaretlenir ve `override_neden` ile `override_kullanici_id` (supervisor) zorunlu olur.
- Toplama tamamlandiktan sonra palet aktif olarak siparise rezerve edilmistir; palet rezervasyonu `Aktif` durumundadir.
- `Tamamlandi` durumuna gecis tam koli zorunlulugu varsayilarak yapilir; kismi koli ozel kosul gerektirir.
- Toplama gorevleri bir `sira_no` ile sirali calistirilir; sira_no urunden urune ve sevkiyat kapsamina gore degisir.

## Adimlar

1. Siparis `Hazirlaniyor` durumuna gecince sistem siparis kalemlerine gore toplama gorevleri olusturur. Her gorev bir palet onerisi tasir (FEFO).
2. Her palet icin **Palet Rezervasyonu** `Aktif` olarak acilir; bu palet baska siparise atanamaz.
3. Operator mobil terminalden gorev havuzunu acar, kendine uygun gorevi ceker. Gorev `Atandi` durumuna gecer.
4. Operator paleti raftan alir; gorev `DevamEdiyor` durumuna gecer.
5. Operator paleti toplama alanina/yukleme kapisina goturur ve gorevi tamamlar. `Tamamlandi` durumuna gecis yapilir.
6. Operator onerilen palet disinda farkli bir palet secerse (orn. en yakin SKT'li palet erisilemez konumda) supervisor `fefo_override` isaretiyle override yapar; gerekce kaydedilir.
7. Toplama tamamlandiktan sonra paletler sevkiyat plani kapsaminda yukleme icin hazirdir; gercek cikis stok hareketi sevkiyat baslayinca yazilir.

## Istisnalar

- **Iptal:** Gorev her aktif durumda iptal edilebilir; iptal nedeni kaydedilir. Iptal sonrasi palet rezervasyonu duzenleme gerektirebilir.
- **Operatore atanmis ama paletin durumu degisti:** Palet karantinaya alindi ya da baska sebepten kullanilamaz hale geldiyse, sistem gorevi iptal etmek ve yeni palet onermek durumundadir.
- **FEFO override gerekcesi yoksa override yapilamaz.** Operator override nedeni belirtmeli; bos gerekce kabul edilmez.
- **Tam koli zorunlulugu:** Toplama varsayilan olarak tam koli uzerinden tamamlanir. Kismi koli operasyonel kosullar gerektirebilir.

## Dogrulanmasi Gereken Kurallar

> ⚠️ Asagidaki maddeler kod davranisindan turetildi ancak operasyon ekibince dogrulanmali.

- **`fefo_override` senaryolari:** Hangi durumlarda override kabul edilir (erisilemez palet, kalite, musteri ozel istegi)? Kaynak: `app/core/entities/toplama_gorevi.py`.
- **`sira_no` belirleme:** Toplama sirasi rota optimizasyonu, raf konum dizilimi mi yoksa siparis kalem sirasi mi? Kaynak: `app/application/use_cases/toplama_gorevi_use_cases.py`.
- **Tam koli zorunlulugu:** Kismi koli sevki hangi kosulda mumkun? Kaynak: `app/core/entities/toplama_gorevi.py:tamamla` ve use case katmani.
- **Iptal sonrasi rezervasyon:** Toplama gorevi iptal edilince palet rezervasyonu otomatik IptalEdildi'ye gecer mi? Kaynak: `app/application/use_cases/palet_rezervasyonu_use_cases.py`.
- **Cikis stok hareketi zamanlamasi:** Cikis hareketi toplama tamamlandiginda mi, sevkiyat Yukleniyor'a gectiginde mi yaziliyor? Kaynak: `app/core/entities/sevkiyat_plani.py:_STOK_CIKARILMIS`.

## Ornek Sorular

- Toplama nasil yapilir?
- Pick gorevi nasil aliniyor?
- Operator FEFO disinda farkli palet alabilir mi?
- FEFO override icin ne gerekir?
- Toplama gorevi neden iptal oldu?
- Bir palet baska bir siparis icin reservation'da, ne yapmaliyim?
- Toplanmis palet stoktan ne zaman dusuyor?
- Toplama sirasi nasil belirleniyor?

## Kisa Cevap Ozeti

Toplama, siparis icin paletlerin raftan toplanmasi surecidir. Sistem FEFO onceligiyle palet onerir, gorev havuzdan operatorca cekilir, palet alinir ve toplama alaninda gorev tamamlanir. FEFO disinda palet seciminde `fefo_override` ve gerekce zorunludur. Toplama tamamlandiktan sonra paletler sevkiyat icin yuklemeye hazir; gercek cikis hareketi sevkiyat baslayinca yazilir.

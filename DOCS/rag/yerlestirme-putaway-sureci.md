---
id: yerlestirme-putaway-sureci
audience: operator
aliases:
  - yerlestirme
  - putaway
  - raf atama
  - paleti rafa koyma
  - yerlesim
related:
  - glossary
  - mal-kabul-sureci
  - toplama-pick-sureci
  - sistem-genel-bakis
updated: 2026-05-13
verified: false
---

# Yerlestirme (Putaway) Sureci

## Amac

Yerlestirme, mal kabul sonrasi her paletin uygun bir rafa konulmasi surecidir. Sistem her palet icin bir yerlestirme gorevi olusturur ve algoritmik olarak bir raf onerir. Operator gorevi havuzdan alir, paleti fiziksel olarak tasir ve onerilen ya da uygun bir rafa onaylayarak yerlestirir.

Kullanici "yerlestirme nasil yapilir", "putaway", "raf atama", "AGV gorevi", "gorev timeout", "override" konularini sordugunda asistan bu dokumana basvurmalidir.

## Kapsam

- Kapsama giren isler:
  - Mal kabul onayindan sonra olusan yerlestirme gorevlerinin akisi.
  - Operatorun gorevi havuzdan cekmesi (pull-based) ve tamamlamasi.
  - Algoritma onerisinden farkli rafa yerlestirme (override) durumlari.
  - Karantina cikislari ve transfer gorevleri.
  - AGV/AMR uzerinden yerlestirme.
- Kapsam disi isler:
  - Toplama (pick) gorevleri (toplama-pick-sureci dokumaninda).
  - Sevkiyat plani ve cikis hareketleri.
  - Spesifik raf onerisi algoritmasinin detayli kosullari.

## Temel Kurallar

- Gorev tipleri: **Yerlestirme** (mal kabul sonrasi normal), **Transfer** (karantina cikis veya zon-arasi), **BelirsizKonum** (veri migrasyonu icin staging cikisi).
- Gorev durum makinesi: **Bekliyor** → **Atandi** → **DevamEdiyor** → **Tamamlandi**. Iptal her aktif durumdan mumkundur.
- Pull-based atama: Gorev sistem tarafindan zorla atanmaz; operator havuzdan kendisi ceker. `Atandi` durumu kilitlidir, baska operator gorevi alamaz.
- `Atandi` durumundan operator gorevi `Bekliyor`'a iade edebilir (bizim sahada "birakma" denilir).
- `DevamEdiyor` durumuna gecis operatorun paleti fiziksel olarak aldigi andir.
- `Tamamlandi`'ya gecis raf okutma ile yapilir; raf okutulmadan tamamlanmaz.
- Operator algoritmanin onerdigi rafa yerlestirebilecegi gibi farkli bir rafa da yerlestirebilir. Farkli raf ise `onerilen_raf_farkli_mi()` true doner; bu durum loglanir.
- Override (kapasite/zon kuralini ihlal eden farkli raf) icin **supervisor** onayi ve `override_neden` zorunludur.
- Bir gorev belirli sure icinde tamamlanmazsa zaman asimina ugrar ve havuza geri donebilir (timeout dakikasi konfigurasyonda).
- Tamamlanan gorev sayisi irsaliye seviyesinde takip edilir; bir mal kabul irsaliyesinin tum gorevleri bitince irsaliye sistem tarafindan **Kapandi** durumuna gecer.

## Adimlar

1. Mal kabul irsaliyesi onaylanir; her kalem icin bir yerlestirme gorevi `Bekliyor` durumunda havuza dusurulur. Her gorev icin algoritma bir `onerilen_raf_id` belirler.
2. Operator mobil terminalden veya depocu ekranindan kendine en uygun gorevi havuzdan ceker. Gorev `Atandi` durumuna gecer; `atanma_tarihi` set edilir.
3. Operator paleti fiziksel olarak alir; gorev `DevamEdiyor` durumuna gecer (`baslama_tarihi` set edilir).
4. Operator paleti onerilen rafa (veya uygun gordugu farkli bir rafa) goturur, raf barkodunu okutarak yerlestirmeyi onaylar.
5. Sistem `Tamamlandi` durumuna gecirir; `gerceklesen_raf_id` ve `tamamlanma_tarihi` kaydedilir. Palet durumu `Yerlestirildi` olur.
6. Operator onerilen rafa yerlestiremedi ve farkli raf kapasite/zon kuralini ihlal ediyor ise: supervisor onayi ile `override_ile_tamamla` cagrilir; `override_neden` ve `override_kullanici_id` kaydedilir.
7. Operator gorevi tamamlayamaz veya baska bir oncelige geciyorsa `Bekliyor` durumuna birakir; atama bilgisi temizlenir, baska operator alabilir.
8. Karantina cikislari icin **Transfer** tipinde gorev olusur (kaynak_raf_id mevcut konum, onerilen_raf_id hedef); ayni durum makinesi izlenir.

## Onerilen Raf Disinda Farkli Rafa Yerlestirme

**Onerilen raf disinda farkli rafa yerlestirebilir miyim?** Evet. Operator algoritmanin onerdigi rafa zorunlu degildir; uygun gordugu farkli bir rafa paleti yerlestirebilir. Bu durumda sistem `gerceklesen_raf_id` alanini operatorun secimi ile doldurur ve `onerilen_raf_farkli_mi()` bayragi ile farki kaydeder.

Iki senaryo vardir:

- **Serbest farklilik:** Onerilen raf disinda secilen yeni raf kapasite ve zon kurallarini ihlal etmiyorsa operator ek onay gerektirmeden raf okutarak gorevi tamamlar.
- **Override gerektiren farklilik:** Onerilen raf disinda secilen raf kapasite veya zon kuralini ihlal ediyorsa **supervisor onayi** gerekir. `override_ile_tamamla` kullanilir; `override_kullanici_id` (supervisor) ve `override_neden` zorunludur. Bos gerekce kabul edilmez.

Override edilen tum gorevler audit icin loglanir; raf onerisi algoritmasinin iyilestirilmesinde bu veriler kullanilir.

## Istisnalar

- **Zaman asimi:** `Atandi` durumundayken belirli sure icinde `DevamEdiyor`'a gecilmezse gorev otomatik havuza dondurulur. Operator gorevi farkinda olmadan birakirsa kayip yasanmaz.
- **Iptal:** Bir gorev her aktif durumda iptal edilebilir (`iptal_nedeni` zorunlu olabilir). Iptal sonrasi palet manuel mudahale gerektirir.
- **Override:** Onerilen rafa farkli rafa yerlestirme normalde serbesttir; ancak kapasite veya zon kurali ihlal ediliyorsa supervisor onayi gerekir.
- **Eksik bilgi:** Eger palet barkodu okunamiyor veya kalem palet ile esleshmiyorsa operator gorevi tamamlamamali; durum operasyon sorumlusuna iletilmelidir.

## Dogrulanmasi Gereken Kurallar

> ⚠️ Asagidaki maddeler kod davranisindan turetildi ancak operasyon ekibince dogrulanmali.

- **Onerilen raf algoritmasi:** Kapasite/zon/lot-yakinligi/SKT/FIFO kriterlerinin sirasi ve agirligi domain servis katmaninda; bu dokumanda yuksek seviye anlatildi. Kaynak: `app/core/services/` altindaki yerlestirme servisi.
- **Timeout dakikasi:** `zaman_asimina_ugradi(timeout_dk)` parametre alir; default deger konfigurasyondan. Operasyonel deger (orn. 15 dk) dogrulanmali. Kaynak: `app/core/entities/yerlestirme_gorevi.py:zaman_asimina_ugradi`.
- **Override yetkili rolu:** `override_kullanici_id` supervisor kaydeder; "supervisor" admin rolu mu yoksa ayri bir rol mu? Kaynak: `app/core/entities/yerlestirme_gorevi.py:override_ile_tamamla`.
- **BelirsizKonum gorev tipi:** Bu tip yalniz veri migrasyonu sirasinda mi olusuyor, yoksa bazi senaryolarda hala mi olusturuluyor? Kaynak: `app/core/entities/yerlestirme_gorevi.py:GorevTipi.BELIRSIZ_KONUM`.
- **AGV gorev cevirimi:** Bir yerlestirme gorevi hangi kosulda insan operatore, hangi kosulda AGV'ye dusuyor? Kaynak: `app/application/use_cases/agv_yerlestirme_tamamla_use_case.py`.
- **Karantina cikis yetki kontrolu:** `Palet.karantinadan_cikar()` durum gecisi yapiyor; kim onaylayabilir kuralini hangi use case uyguluyor? Kaynak: `app/application/use_cases/palet_use_cases.py`.

## Ornek Sorular

- Yerlestirme gorevi nasil olusuyor?
- Putaway sureci nedir?
- Bir paleti onerilen raf disinda farkli bir rafa yerlestirebilir miyim?
- Override icin ne gerekir?
- Gorev neden iptal edildi?
- Operator gorevi neden goremiyor?
- Karantinaya alinmis palet nasil cikar?
- Mal kabul irsaliyesi neden hala Kapandi'ya gecmiyor?
- AGV gorevi nasil ataniyor?
- Yerlestirme gorevi zaman asimina ugrarsa ne olur?

## Kisa Cevap Ozeti

Yerlestirme, mal kabul sonrasi her paletin uygun rafa konulma surecidir. Sistem her kalem icin bir gorev olusturur ve raf onerir; operator gorevi havuzdan pull-based ceker, paleti alir ve raf okutarak tamamlar. Operator algoritma onerisinden farkli rafa yerlestirebilir; kapasite/zon ihlali olursa supervisor override ve gerekce zorunludur. Tum gorevler tamamlandiginda mal kabul irsaliyesi otomatik Kapandi'ya gecer.

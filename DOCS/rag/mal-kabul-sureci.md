---
id: mal-kabul-sureci
audience: operator
aliases:
  - mal kabul
  - mal girisi
  - kabul sureci
  - giris irsaliyesi
  - tedarikci kabul
  - inbound
related:
  - glossary
  - yerlestirme-putaway-sureci
  - sistem-genel-bakis
updated: 2026-05-13
verified: false
---

# Mal Kabul Sureci

## Amac

Mal kabul, tedarikciden gelen veya uretimden inen urunlerin depoya sistemli sekilde alinmasi surecidir. Amac, gelen her paletin urun, lot, son kullanma tarihi ve miktar bilgileriyle birlikte sisteme kaydedilmesi, onay sonrasinda yerlestirme gorevlerinin otomatik olusturulmasi ve stoga dahil edilmesidir.

Kullanici mal kabul, giris irsaliyesi, tedarikci kabul, hizli kabul, istisna bildirimi (eksik/fazla/hasarli) konularinda soru sordugunda asistan bu dokumana basvurmalidir.

## Kapsam

- Kapsama giren isler:
  - Tedarikci tirinden inen paletlerin mal kabul irsaliyesine kalem olarak girilmesi.
  - Mal kabul irsaliyesinin Taslak'tan Onaylandi'ya gecirilmesi.
  - Onay sonrasi yerlestirme gorevlerinin otomatik olusturulmasi.
  - Kalem bazinda istisna bildirimi (Eksik, Fazla, Hasarli, YanlisUrun, OkunamazBarkod, Diger).
  - Uretim paletlerinin (kaynak=uretim) kabulu (saha hizli kabul veya KabulBekliyor uzerinden).
- Kapsam disi isler:
  - Yerlestirme algoritmasi ve raf secimi (yerlestirme-putaway-sureci dokumaninda).
  - Sevkiyat ve cikis hareketleri.
  - DocAiService'in irsaliye PDF/JPG'den taslak cikarmasi (kullanici icin saydam; bu doc sadece operator gozunden anlatir).

## Temel Kurallar

- Mal kabul irsaliyesi uc durumdan birinde bulunur: **Taslak** (duzenlenebilir), **Onaylandi** (yerlestirme baslar), **Kapandi** (tum yerlestirme gorevleri tamamlanmis, sistem otomatik gecirir).
- Kalemsiz bir irsaliye onaylanamaz.
- Sadece **Taslak** durumundaki irsaliyeye kalem eklenebilir veya degistirilebilir.
- **Kapandi** durumuna gecisi yalniz sistem yapar; kullanici manuel kapatma yapamaz.
- Kalem durumu **Bekliyor** veya **GirisYapildi** seklindedir; giris yapilmis kaleme tekrar giris yapilamaz.
- Istisna tipleri sabittir: `Eksik`, `Fazla`, `Hasarli`, `YanlisUrun`, `OkunmazBarkod`, `Diger`. Bunlardan disindaki bir tip kabul edilmez.
- Uretim paletinde durum makinesi su sekildedir: `Olusturuldu` → `KabulBekliyor` veya direkt `KabulEdildi` (barkod okutma ile saha hizli kabul). `IptalEdildi` olan palet yeniden etiket gerektirmeden kabul edilemez.
- Kabul edilen palet stoga girer; `kabul_eden_kullanici_id` ve `kabul_tarihi` denetim icin kaydedilir.

## Adimlar

1. Tedarikci tiri depoya yanasir; tir plaka ve sofor bilgileri irsaliye uzerine yazilir.
2. Yetkili kullanici **Taslak** durumunda yeni mal kabul irsaliyesi acar (tedarikci, depo, tarih).
3. Her palet icin bir kalem eklenir: palet_no, urun, lot_no, miktar, varsa uretim/son kullanma tarihi.
4. Tum kalemler girildikten sonra irsaliye **Onaylandi** durumuna gecirilir. Onaylama anlik olarak:
   - Her kalem icin bir **Yerlestirme Gorevi** havuza dusurur.
   - Paletlerin durumunu `KabulEdildi` yapar; stok girisi tetiklenir.
5. Bir kalemde fiziksel uyumsuzluk varsa (eksik, fazla, hasarli vb.) istisna bildirilir; istisna tipi ve aciklama kaydedilir.
6. Yerlestirme gorevleri tamamlandikca irsaliyenin yerlestirme ozeti guncellenir. Tum gorevler tamamlandiginda sistem irsaliyeyi otomatik **Kapandi** durumuna gecirir.
7. Uretim palet akisinda saha kullanicisi barkod okutarak `Olusturuldu` paletini dogrudan `KabulEdildi`'ye gecirebilir (hizli kabul) ya da kayit asamasinda `KabulBekliyor` durumundan kabul yapilir.

## Istisnalar

- **Hasarli palet geldiginde:** Bir palet hasarli olarak geldiginde operator kalemde **istisna bildirir**: istisna tipi `Hasarli`, aciklama (orn. "palet 3 kosesi kirik") ve varsa fark miktari kaydedilir. Hasarli palet normalde dogrudan yerlestirilmez; karantinaya alinma veya iade akisi operasyon sorumlusunun karari ile yonetilir.
- **Eksik veya fazla urun:** Fiziksel miktar irsaliyedekiyle uyusmazsa kalemde `Eksik` veya `Fazla` istisnasi bildirilir; gerceklesen miktar yazilir.
- **Yanlis urun:** Irsaliyede beklenen urunden farkli urun gelirse `YanlisUrun` istisnasi bildirilir; operasyon sorumlusu karariyla iade veya kabul yapilir.
- **Okunamayan barkod:** Palet veya urun barkodu okunamiyorsa `OkunmazBarkod` istisnasi bildirilir; operator manuel kayit veya yeniden etiketleme akisi izler.
- **Kalemsiz onaylama:** Hicbir kalem girilmeden onay denenirse sistem onayi reddeder.
- **Tekrar giris:** Zaten `GirisYapildi` durumundaki kaleme yeniden giris denemesi reddedilir.
- **Iptal palet kabulu:** `IptalEdildi` durumundaki bir palet yeniden etiket olmadan kabul edilemez.
- **Onaylanmis irsaliyede degisiklik:** `Onaylandi` veya `Kapandi` durumundaki irsaliyede kalem eklemek/silmek mumkun degildir.
- **Istisna bildirimi:** Istisna kaleminin yerlestirme gorevine girip girmedigi istisna tipine bagli olabilir; supheli durumda kullanici operasyon sorumlusuna danismalidir.

## Dogrulanmasi Gereken Kurallar

> ⚠️ Asagidaki maddeler kod davranisindan turetildi ancak operasyon ekibince dogrulanmali. Asistan bu maddeleri kullaniciya iletirken "operasyon ekibince dogrulanmasi gerekir" notunu eklemelidir.

- **Minimum kalem kurali:** Kod yalniz "kalem listesi bos olmamali" kuralini uyguluyor; tedarikci alanlarinin (tir plaka, sofor, vs.) zorunlu olup olmadigi belirsiz. Kaynak: `app/core/entities/mal_kabul_irsaliye.py:onayla`.
- **Onaylanmis irsaliyede duzenleme yetkisi:** `Onaylandi` durumunda iptal/duzeltme icin ozel supervisor yetkisi var mi, yoksa hic mi degisiklik kabul edilmiyor? Kaynak: `app/core/entities/mal_kabul_irsaliye.py:duzenlenebilir_mi`.
- **Istisna kaleminin akisi:** `Eksik`/`Fazla`/`Hasarli` istisnasi olan kalemler yerlestirme gorevine donusur mu, dogrudan karantinaya mi gider, yoksa irsaliye duzeltilmeden bekler mi? Kaynak: `app/core/entities/mal_kabul_irsaliye.py:istisna_bildir`.
- **KabulBekliyor uzerinden kabul:** Saha hizli kabul varken `KabulBekliyor` durumu hangi senaryoda fiilen kullaniliyor? Kaynak: `app/core/entities/palet.py:UretimPaletDurum`.

## Ornek Sorular

- Mal kabul nasil yapilir?
- Mal kabul irsaliyesi onaylanmadan once neler yapilmali?
- Onaylandiktan sonra irsaliye degistirilebilir mi?
- Bir palet hasarli geldiginde nasil islem yapilir?
- Eksik gelen urun icin ne yapilmali?
- Mal kabul irsaliyesi neden Kapandi durumuna gecmiyor?
- Uretim paletini saha kabulu nasil yapilir?
- Mal kabul irsaliyesinde hangi alanlar zorunlu?

## Kisa Cevap Ozeti

Mal kabul, gelen paletlerin sisteme kaydi ve onay surecidir. Irsaliye Taslak'ta acilir, her palet kalem olarak girilir, onaylandiktan sonra yerlestirme gorevleri otomatik olusur ve palet stoga girer. Tum yerlestirme gorevleri bittiginde irsaliye sistem tarafindan otomatik Kapandi'ya gecer. Eksik, fazla, hasarli gibi durumlar kalem bazinda istisna olarak bildirilir.

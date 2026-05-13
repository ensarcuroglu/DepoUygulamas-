---
id: sevkiyat-sureci
audience: operator
aliases:
  - sevkiyat
  - sevk
  - cikis
  - tir yukleme
  - musteri gonderim
  - sevkiyat plani
related:
  - glossary
  - toplama-pick-sureci
  - sistem-genel-bakis
  - fefo-sureci
updated: 2026-05-13
verified: false
---

# Sevkiyat Sureci

## Amac

Sevkiyat, toplanan paletlerin siparis kapsaminda musteriye yola cikarilmasi surecidir. Sevkiyat plani uzerinde tir plaka, sofor, kapi ve yukleme tarihi bilgileri tanimlanir; tir yanasinca palet yukleme baslar, arac yola cikar ve musteriye teslim edilir. Bu sirada cikis stok hareketleri ve siparis durum gecisleri otomatik isler.

Kullanici "sevkiyat nasil yapilir", "tir yukleme", "cikis hareketi", "sevkiyat durumu", "plaka degisikligi", "rezervasyon kesinlesmesi" konularini sordugunda asistan bu dokumana basvurmalidir.

## Kapsam

- Kapsama giren isler:
  - Bir siparis icin sevkiyat plani olusturulmasi.
  - Sevkiyat durum makinesi (Planlandi → Yukleniyor → Yolda → TeslimEdildi).
  - Tir/sofor/kapi meta alanlarinin duzenlenebilirlik kosullari.
  - Cikis stok hareketinin tetiklenmesi.
  - Palet rezervasyonlarinin kesinlestirilmesi.
- Kapsam disi isler:
  - Toplama (pick) gorevlerinin olusumu (toplama-pick-sureci dokumaninda).
  - Sipariste fiyat/musteri yonetimi.
  - Sevkiyat sonrasi iade yonetimi.

## Temel Kurallar

- Sevkiyat plani durumlari: **Planlandi**, **Yukleniyor**, **Yolda**, **TeslimEdildi**. Gecisler tek yonludur; geri donus yoktur.
- `Planlandi` → `Yukleniyor` → `Yolda` → `TeslimEdildi` sirasi disinda gecis kabul edilmez.
- Sevkiyat bir siparise birebir baglidir (`siparis_id`). Sevkiyat kalemleri siparis kalemlerinden 1:1 kopyalanir.
- **Yukleniyor**, **Yolda** ve **TeslimEdildi** durumlarinda paletler "stok cikarilmis" sayilir; bu durumlardaki sevkiyatlar stok cikis raporlarinda gorunur.
- Meta alanlar (plaka, sofor, kapi, tarih, saat) yalniz `Planlandi` ve `Yukleniyor` durumlarinda degistirilebilir; `Yolda` ve `TeslimEdildi`'de duzenlenemez.
- `TeslimEdildi` tum alanlari kilitler; bu durumda hicbir alan duzenlenemez.
- Sevkiyat tamamlaninca (`TeslimEdildi`) bagli palet rezervasyonlari `Kesinlesti` durumuna gecirilir.
- Siparis durumu sevkiyat akisina paralel ilerler: `Hazirlaniyor` → `YolaCikti` → `TeslimEdildi`.

## Adimlar

1. Siparis `Hazirlaniyor` durumuna gecip toplama gorevleri olusturuldugunda, ilgili siparis icin **Sevkiyat Plani** olusturulabilir. Durum: `Planlandi`. Bos plaka/sofor alanlari sonradan doldurulabilir.
2. Tir bilgisi netleserek plaka, sofor adi/telefonu, depo kapisi, yukleme tarihi ve cikis saati plana yazilir.
3. Tir yanasinca durum `Yukleniyor`'a gecirilir. Toplanmis paletler tira yuklenir; bu durumdaki sevkiyat stok cikis akisina dahil edilir.
4. Yukleme tamamlanip arac depodan ayrildiginda durum `Yolda`'ya gecer. Bu noktadan sonra meta alanlar kilitlenir.
5. Musteri/sofor teslimati onayladigi anda durum `TeslimEdildi`'ye cekilir. Tum alanlar kilitlenir; palet rezervasyonlari kesinlesir; siparis `TeslimEdildi` durumuna gecer.
6. Acil durumda (orn. arac arizasi) sevkiyat ileri sarilir veya iade akisi devreye girer; ancak `TeslimEdildi`'den geri donus olmaz, duzeltme yeni belge ile yapilir.

## Istisnalar

- **Geri donus yok:** Sevkiyat ileri yondedir. Yanlislikla `Yolda` yapilan sevkiyat sistemde geri alinmaz; manuel duzeltme operasyon sorumlusu ile yapilir.
- **Meta alan kilitleme:** Plaka veya sofor degisikligi `Yolda` durumunda sistemden yapilamaz. Acil sofor degisimi varsa operasyon sorumlusuna danisilmalidir.
- **Kismi yukleme:** Bir siparisin tum kalemleri toplanmadan sevkiyat baslatilirsa kalan kalemler sonraki sevkiyatla gider; ancak bu kosulun sistemde otomatik destekleyip desteklemedigi operasyona bagli.
- **Iptal:** Sevkiyat plani iptal akisi standart durum makinesinde yer almaz; iptal gerekirse siparis seviyesinde mudahale ve manuel duzeltme yapilir.

## Dogrulanmasi Gereken Kurallar

> ⚠️ Asagidaki maddeler kod davranisindan turetildi ancak operasyon ekibince dogrulanmali.

- **Yukleniyor → Yolda dogrulamasi:** Kapi kontrolu, palet sayim onayi veya tarti gibi fiziksel dogrulamalar gerekiyor mu? Kaynak: `app/core/entities/sevkiyat_plani.py:_GECISLER`.
- **Cikis stok hareketi zamani:** `_STOK_CIKARILMIS = {Yukleniyor, Yolda, TeslimEdildi}` setine gore palet `Yukleniyor`'da cikmis sayiliyor; gercek stok hareketi `StokHareketi` kaydi hangi durum gecisinde yaziliyor? Kaynak: `app/application/use_cases/stok_hareketi_use_cases.py`.
- **Rezervasyon kesinlestirme zamani:** `PaletRezervasyonu.kesinlestir()` hangi sevkiyat gecisinde tetikleniyor — Yukleniyor mu, TeslimEdildi mi? Kaynak: `app/application/use_cases/palet_rezervasyonu_use_cases.py`.
- **Meta degisiklik istisnasi:** `Yolda` durumunda acil sofor degisimi icin ozel bir override var mi? Kaynak: `app/core/entities/sevkiyat_plani.py:meta_duzenlenebilir_mi`.
- **Iptal akisi:** Sevkiyat plani iptal etmek standart endpoint'ten mi yoksa siparis iptali ile mi yapiliyor? Kaynak: `app/application/use_cases/sevkiyat_plani_use_cases.py`.
- **Kismi yukleme destegi:** Bir siparisin kismen yuklenip kalan kalemler ikinci sevkiyatla gitmesi sistemde nasil modelleniyor? Kaynak: `app/core/entities/sevkiyat_plani.py:SevkiyatKalemi`.

## Ornek Sorular

- Sevkiyat nasil baslar?
- Sevkiyat plani durumlari nelerdir?
- Tir plaka sevkiyat sirasinda degistirilebilir mi?
- Cikis stok hareketi ne zaman yaziliyor?
- Sevkiyat tamamlandiktan sonra siparis durumu ne olur?
- TeslimEdildi olan sevkiyatta duzeltme yapilabilir mi?
- Palet rezervasyonu ne zaman kesinlesir?
- Sevkiyat plani neden Yukleniyor'a gecemiyor?

## Kisa Cevap Ozeti

Sevkiyat, toplanan paletlerin tira yuklenip musteriye gonderilme surecidir. Plan Planlandi'da acilir, tir gelince Yukleniyor'a gecer (stok cikis akisi baslar), arac yola cikinca Yolda olur (meta alanlar kilitlenir) ve teslim onayinda TeslimEdildi durumuna gecer (palet rezervasyonlari kesinlesir, siparis kapanir). Geri donus yoktur; duzeltmeler yeni belge ile yapilir.

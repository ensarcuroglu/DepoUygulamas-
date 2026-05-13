---
id: sistem-genel-bakis
audience: operator
aliases:
  - sistem nasil calisir
  - genel bakis
  - is akisi
  - sistemin isleyisi
  - depo akisi
related:
  - glossary
  - mal-kabul-sureci
  - yerlestirme-putaway-sureci
  - toplama-pick-sureci
  - sevkiyat-sureci
  - fefo-sureci
updated: 2026-05-13
verified: false
---

# Sistem Genel Bakis

## Amac

Bu dokuman, WMS'in operator gozunden nasil calistigini tek bir akista ozetler. **Bir paletin depoya girisinden cikisina kadar gecen surec** (mal kabul → yerlestirme → toplama → sevkiyat), hangi rollerin hangi adimlari yaptigini ve modullerin nasil birbirine baglandigini anlatir. Bir paletin yasam dongusu, sistemdeki tipik gun akisi ve genel isleyis bu dokumandan ogrenilir. Kullanici "sistem nasil isliyor", "genel akis nedir", "paletin depoya girisinden cikisina kadar nasil bir surec isler", "hangi modul ne yapar", "kim hangi ekrani gorur" gibi sorular sordugunda asistan bu dokumana basvurmalidir.

Bu doc temel akisi ozetler; her surec icin detay ayri dokumanda yer alir (mal kabul, yerlestirme, toplama, sevkiyat, FEFO).

## Kapsam

- Kapsama giren isler:
  - Mal kabulden sevkiyata kadar tipik bir gun akisi.
  - Operator rolleri ve kullandiklari ekranlar.
  - Modullerin yuksek seviye iliskisi (terminal, AGV, LMS, AI asistani).
- Kapsam disi isler:
  - Tekil surecler icin detay kurallar (ilgili dokumanlara yonlendirilir).
  - Teknik kurulum, deployment, mimari.
  - Spesifik hata kodlari ve cozumleri.

## Temel Kurallar

- Sistem palet/lot bazli izlenebilirlik uzerine kuruludur; her urun bir lota, her lot uretilmis palete baglidir.
- Stok hareketleri (giris/cikis) her zaman bir kullanici ve bir bag (irsaliye_no veya siparis_no) ile yazilir.
- Operatorler gorevleri pull-based ceker: havuzda bekleyen gorevi kendileri sahiplenir, sistem zorla atamaz.
- FEFO kurali tum cikis (toplama, sevkiyat) onerilerinin temelidir; override yapilirsa gerekce zorunludur.
- Roller arasi yetki sinirlidir: depocu mobil terminal ve operasyon ekranlarini, lojistik depo/sevkiyat ekranlarini, admin tum yonetim ekranlarini gorur.

## Adimlar

Bir paletin yasam dongusunde tipik akis su sekildedir:

1. **Mal kabul**: Tedarikci tirinden inen veya uretimden gelen paletler icin mal kabul irsaliyesi olusturulur. Operator/yetkili her paleti kalem olarak girer (palet_no, urun, lot_no, miktar). Irsaliye Taslak durumundadir.
2. **Onay**: Tum kalemler girildikten sonra irsaliye onaylanir. Bu noktada her kalem icin bir yerlestirme gorevi olusur ve palet KabulEdildi durumuna gecer.
3. **Yerlestirme (Putaway)**: Yerlestirme gorevleri havuza dusurulur. Operator mobil terminal/depocu ekranindan gorevi ceker (Atandi), paleti alir (DevamEdiyor), onerilen rafa goturur ve raf okutarak tamamlar (Tamamlandi). Palet Yerlestirildi olur. Tum gorevler tamamlanan irsaliye otomatik Kapandi durumuna gecer.
4. **Siparis ve toplama**: Musteri siparisi geldiginde (Bekleme → Hazirlaniyor) sistem FEFO onceligine gore toplama gorevleri olusturur. Operator gorevi ceker, paletleri toplar ve sevkiyat hazirligi yapar.
5. **Sevkiyat**: Siparis icin sevkiyat plani acilir (Planlandi). Tir gelince yukleme baslar (Yukleniyor — bu noktada cikis stok hareketi yazilir), arac yola cikar (Yolda) ve teslimat onayindan sonra TeslimEdildi olur. Palet rezervasyonlari kesinlesir, siparis YolaCikti/TeslimEdildi durumuna ilerler.
6. **Sayim ve duzeltme**: Periyodik veya emir ile stok sayimi yapilir; fark cikarsa duzeltme stok hareketi olarak yazilir.
7. **Karantina ve blokaj**: Hasarli, kalite kontrol bekleyen veya supheli paletler Karantina'ya alinir; bu paletler normal toplamaya girmez, yetkili onayi olmadan cikis yapamaz.

## Roller

> ⚠️ DOĞRULANMASI GEREKEN KURAL: Asagidaki rol-ekran eslesmesi kod ve route guard'larindan turetildi. Operasyon ekibinin gercek is bolumunu netlestirmesi gereklidir (kaynak: `ReactProje/src/components/RoleRoute.jsx`, `BackendProje/app/api/v1/routers/*` auth katmani).

- **admin**: Yonetim ekranlari, raporlama, ayarlar, kullanici yonetimi, tum operasyon ekranlari. Override yetkisi olabilir.
- **depocu**: Mobil terminal, depocu ekranlari, palet kabul, yerlestirme, toplama gorevleri, uretim paleti kabul. `/depocu/*` rotalari yalniz bu role aciktir.
- **lojistik**: Depolar, depo kroki, stok hareketleri, sevkiyat plani ekranlari.
- **goruntuleyen**: Salt okunur erisim. Hicbir is akisi tetikleyemez, yalniz raporlari ve listeleri gorur.

## Moduller

- **Backend (FastAPI)**: Tum is mantigi ve veri yonetiminin sahibi. Mal kabul, yerlestirme, toplama, sevkiyat, sayim, rezervasyon use case'leri burada calisir.
- **Mobil terminal (PWA)**: Depocu icin barkod okutma, gorev cekme, raf onaylama. Web tarayicidan veya mobil cihazdan ayni adres uzerinden erisilir.
- **AGV / AMR servisi**: Bazi yerlestirme/transfer gorevlerini otonom robotlarla yapar. Backend gorev gonderir, AGV servisi geri callback ile tamamlandigini bildirir.
- **Belge AI (DocAiService)**: Tedarikci irsaliyesinin PDF/JPG'sinden taslak kalem cikarir (palet_no, urun, miktar). Veritabanina yazmaz; sadece backend'e taslak doner, operator inceleyip onaylar.
- **LMS (Operator Performans)**: Yerlestirme ve toplama bitislerinden olay alir, vardiya bazinda UPH ve KPI hesaplar, operator leaderboard'u uretir.
- **AI Asistani**: Kullanici sorularini iki rotaya yonlendirir. Veri/sayim sorulari (kac palet, hangi urun, son 7 gun) icin SQL uretir; surec/tanim sorulari icin bu dokumantasyondan cevap dondurur.

## Istisnalar

- Asistan, role veya yetkiye gore kullaniciya farkli cevap vermez. Yetki kontrolu sistemin kendisindedir.
- Operasyonel bir hata ile karsilasilirsa (orn. negatif stok, kapali irsaliyeye kalem ekleme, gecersiz durum gecisi) sistem islemi reddeder; sebebi hata mesajinda belirtir.
- Bu doc spesifik sayisal degerler (timeout suresi, kapasite esikleri, oncelik kategorileri) vermez; bunlar sistem konfigurasyonundan gelir ve operasyon ekibince yonetilir.

## Ornek Sorular

- Sistem nasil calisir?
- Bir paletin depoya girisinden cikisina kadarki yolu nedir?
- Hangi modul ne yapar?
- Mal kabul, yerlestirme, toplama ve sevkiyat nasil baglanir?
- Hangi rol hangi ekranlari gorur?
- AGV ve AI asistani sistemin neresinde duruyor?
- Operator gorevi nasil aliyor?

## Kisa Cevap Ozeti

WMS, palet ve lot bazli izlenebilirlik uzerine kurulu bir depo yonetim sistemidir. Tipik akis su sekildedir: mal kabul irsaliyesi olusturulur ve onaylanir, sistem yerlestirme gorevleri uretir, operator paleti rafa yerlestirir, siparis geldiginde FEFO sirasiyla toplama gorevleri olusur, sevkiyat plani uzerinden tir yuklenir ve cikis stok hareketi yazilir. Operatorler gorevleri kendi pull-based cekerler; admin yonetir, depocu sahada calisir, lojistik depo/sevkiyat tarafini yonetir. Detay icin ilgili surec dokumanlarina bakin.

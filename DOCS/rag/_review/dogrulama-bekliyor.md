# Doğrulanması Bekleyen Kurallar

Bu dosya `DOCS/rag/` altındaki dokümanlarda **kod-türevi yazılmış**, ancak iş kuralı niyeti operasyon ekibince doğrulanmamış maddeleri toplar. Underscore prefix'iyle başladığı için (`_review/`) RAG koleksiyonuna **indekslenmez**; asistan bu içeriği kullanıcıya **döndürmez**.

Doğrulama tamamlandığında ilgili doküman içindeki `> ⚠️ DOĞRULANMASI GEREKEN KURAL` notu kaldırılır, doküman front-matter'ında `verified: true` yapılır ve buradaki ilgili madde silinir.

---

## glossary.md

- (Şimdilik yok — terim tanımları doğrudan entity ve view'lardan türetildi.)

## sistem-genel-bakis.md

- **Operatör rolleri ve ekran eşleşmesi:** `admin`, `depocu`, `lojistik`, `goruntuleyen` rollerinin hangi ekranları gördüğü `BackendProje/app/api/v1/routers/*` ve `ReactProje/src/components/RoleRoute.jsx` üzerinden çıkarıldı. Operasyon ekibinin “lojistik” ve “depocu” arasındaki gerçek iş bölümü doğrulanmalı.

## mal-kabul-sureci.md

- **Taslak → Onaylandi geçişinde minimum kalem sayısı:** Kod sadece `kalemler boş olmamalı` kuralını uyguluyor (`MalKabulIrsaliye.onayla()`); operasyonda “minimum N kalem” ya da “tüm tedarikçi alanları zorunlu” gibi ek kural var mı?
- **Onaylanmış irsaliyede kalem ekleme/değiştirme:** `duzenlenebilir_mi()` sadece TASLAK için True; onaylandıktan sonra hangi alanlar düzenlenebilir, hangi süpervizör yetkisi gerekir — kodda yok.
- **İstisna bildirimi sonrası akış:** `MalKabulKalemi.istisna_bildir(EKSIK|FAZLA|HASARLI|YANLIS_URUN|OKUNAMAZ_BARKOD|DIGER)` — istisna olan kalem yine de yerleştirme görevi oluşturur mu, yoksa istisna türüne göre farklı mı işlenir?
- **Hızlı kabul vs. KabulBekliyor akışı:** `Palet.kabul_et()` hem `OLUSTURULDU`'dan hem `KABUL_BEKLIYOR`'dan KABUL_EDILDI'ye izin veriyor. Saha akışında “KabulBekliyor” durumu hangi senaryoda kullanılıyor?

## yerlestirme-putaway-sureci.md

- **Raf önerisi algoritması:** Kapasite/zon/FIFO/lot-yakınlığı kriterlerinin gerçek sıralaması ve ağırlıkları `app/core/services/` altındaki yerleştirme servisinde; bu dokümanda yüksek seviyede özet geçildi, kesin algoritma operasyon ekibince netleştirilmeli.
- **Görev timeout süresi:** `YerlestirmeGorevi.zaman_asimina_ugradi(timeout_dk)` parametre alıyor; gerçek default değer (örn. 15 dk) konfigürasyonda. Operasyon ekibi onaylasın.
- **Override yetkisi:** `override_ile_tamamla(supervisor_id, neden)` çağrısı için hangi rol yetkili — `admin` mi yoksa ayrı bir “süpervizör” rolü mü?
- **MIGRATION_STAGING ve BelirsizKonum görev tipi:** Bu görev tipi mevcut kabul akışında otomatik oluşur mu yoksa sadece veri migrasyonu zamanında mı kullanıldı?
- **Karantinadan çıkış:** `karantinadan_cikar()` use case katmanında “yetkili onayı” kontrolü yapıyor; hangi rol bu onayı verebilir?

## toplama-pick-sureci.md

- **`fefo_override`:** Operatör FEFO önerisinden farklı bir palet alırsa `fefo_override=True` + `override_neden` zorunlu. Hangi senaryoda override kabul edilir (örn. en yakın SKT'li palet erişilemez konumda)?
- **`sira_no`:** Toplama görevlerinin sıralaması — rota optimizasyonu mu, sevkiyat planındaki kalem sırası mı, palet konumu mu belirliyor?
- **Tam koli zorunluluğu:** `tamamla()` docstring'i “tam koli zorunluluğu use case'de kontrol edilir” diyor; kısmi koli sevki hangi koşulda mümkün?
- **İptal sonrası palet/lot:** Toplama görevi iptal edilirse palet/lot rezervasyonu otomatik serbest kalır mı?

## sevkiyat-sureci.md

- **Yukleniyor → Yolda geçişi:** Kapı kontrolü, dolu palet sayımı veya tartı gibi fiziksel doğrulamalar zorunlu mu?
- **Stok hareketi tetikleme zamanı:** `SevkiyatDurum.stok_cikarilmis_mi()` Yukleniyor/Yolda/TeslimEdildi'yi içeriyor — çıkış hareketi tam olarak hangi durum geçişinde yazılıyor?
- **Rezervasyon kesinleşmesi:** `PaletRezervasyonu.kesinlestir()` hangi sevkiyat durum geçişinde tetikleniyor — Yukleniyor mu, TeslimEdildi mi?
- **Plaka/şoför/kapı değişimi:** `meta_duzenlenebilir_mi()` Planlandi+Yukleniyor için True; Yolda'da hangi durumda meta değişikliği yapılır (örn. acil sürücü değişimi)?

---

## Süreç

1. Bu listeyi operasyon ekibine düzenli aralıklarla iletin (haftalık veya 2. batch öncesi).
2. Cevaplanan her madde için ilgili doküman güncellenir, `> ⚠️ DOĞRULANMASI GEREKEN KURAL` bloğu kaldırılır, doküman front-matter'ında `verified: false` → `verified: true` yapılır.
3. Doküman güncellemesinden sonra `cd WmsAiService && python ingest_docs.py --docs` çalıştırılır.
4. Bu listeden ilgili madde silinir.

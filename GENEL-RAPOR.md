📊 Depo Yönetim Sistemi – Endüstri Standardı Analizi

  ✅ Güçlü Yönler

  Mimari
  - Clean Architecture %100 tamamlanmış (17/17 modül) — domain/application/infrastructure ayrımı net
  - Domain entity'lerde iş kuralları (state machine, geçiş validasyonları) doğru yerde
  - DI container, repository pattern, use case katmanı temiz
  - ERP entegrasyonu için Adapter Pattern (erp_palet_veri_kaynagi_service) — doğru tercih

  Domain Modeli
  - Lot/Palet/Raf/Zon hiyerarşisi endüstri standardına uygun
  - Depolama tipi ↔ Zon tipi uyumluluk matrisi (Kuru/Soğuk/Tehlikeli)
  - Hiyerarşik raf kodu (ZON-KORIDOR-RAF-KAT-GÖZ) — lokasyon izlenebilirliği iyi
  - Putaway görev akışı (Bekliyor→Atandı→DevamEdiyor→Tamamlandı) + override mekanizması
  - Sevkiyat ve Sipariş state machine'leri ayrı ama orkestratör ile senkron (Faz 3)
  - Palet bazlı stok hareketi + irsaliye_no backfill (Faz 5)

  Güvenlik/Altyapı
  - JWT + refresh token rotation (hash ile), bcrypt, rate limiting (slowapi)
  - Rol bazlı + depo bazlı erişim kontrolü (RBAC)
  - Birleşik exception handler, SistemLog audit

  ---
  ⚠️ Eksik / Hatalı / İyileştirilecek Alanlar

  🔴 Kritik Eksikler (Endüstri Standardı WMS gereği)

  1. FEFO/FIFO Pick Enforcement
  Lot.skt_gecmis_mi / skt_yaklasik_mi var ama sevkiyatta otomatik FEFO pick order (en yakın SKT'li lotun       
  zorunlu seçimi) uygulandığına dair net bir servis yok. Gıda/ilaç için kritik.
  2. Pick / Wave Planning
  YerlestirmeGorevi (putaway) var; ancak simetrik ToplamaGorevi (Pick Task) yok. SevkiyatKalemi kopyası var ama
   hangi palet/rafdan toplanacağı görev bazlı değil. Wave picking, batch picking, zone picking yok.
  3. Stok Rezervasyon / Allocation
  Sipariş oluşturulduğunda stok commit edilmiyor görünüyor. Aynı anda iki sipariş aynı paleti alabilir (race   
  condition). Urun.stok_miktari column_property olduğu için anlık hesap — rezerve stok ayrımı yok.
  4. İade / Reverse Logistics (RMA)
  BelgeTuru.IADE_IRSALIYESI enum değeri var ama müşteri iade akışı (RMA → Karantina → QC → Restock / Hurda)    
  workflow entity'si yok.
  5. Kalite Kontrol (QC) Workflow
  ZonTipi.KARANTINA ve karantinadan_cikis_onay_gerekli_mi var; ancak QC test kaydı, numune, onay/red için      
  entity/use case yok. Mal kabul istisnaları (IstisnaKalemTip) tutuluyor ama QC süreciyle bağlantı kopuk.      
  6. Cycle Count (Döngüsel Sayım)
  StokSayim tam sayıma göre tasarlanmış (baslat→bitir→onayla). ABC/XYZ kategorisine göre döngüsel sayım        
  planlaması yok — büyük depolarda tam sayım pratik değildir.
  7. Depo-Arası Transfer
  GorevTipi.TRANSFER sadece zon-arası. Farklı depolar (Depo entity'si çoğul) arası transfer için
  InterWarehouseTransfer entity'si yok.

  🟡 Orta Öncelikli

  8. E-İrsaliye / GİB Entegrasyonu
  Türkiye'de ticari irsaliye için e-İrsaliye (GİB) entegrasyonu zorunlu. Irsaliye entity var, ancak GİB UUID,  
  zarf, cevap kaydı alanları yok.
  9. Slotting Optimization
  Algoritmanın onerilen_raf_id doldurduğunu görüyoruz ama ABC/hız bazlı yerleştirme stratejisi kodlanmış mı    
  belirsiz. Sadece kapasite/zon-tipi kontrolü yapıyor gibi.
  10. Dock / Kapı Randevu (Appointment)
  depo_kapi bir string alan; çakışma kontrolü, dock planlama takvimi yok.
  11. KPI Dashboard — Outbound
  InboundDashboardPage + KpiDashboardPage var. Ama standart KPI'lar (OTIF, Inventory Accuracy, Dock-to-Stock,  
  Pick Accuracy, Order Cycle Time) formülleri kesin tanımlı mı belirsiz.
  12. Concurrency / Locking
  Putaway görevini "pull-based FIFO" olarak alıyor operatör — ancak DB seviyesinde SELECT ... FOR UPDATE SKIP  
  LOCKED kullanımı görünmüyor. İki operatör aynı görevi çekebilir.
  13. Idempotency
  POST /siparisler/, /mal-kabul/onayla gibi kritik uçlarda idempotency key yok → retry'da çift kayıt riski.    
  14. Rapor/Audit Immutability
  StokHareketi silinebilir/güncellenebilir mi? Audit log için append-only olmalı (DB trigger /
  application-layer enforcement).

  🟢 Teknik Borç / İyileştirme

  15. datetime.utcnow() deprecation
  Python 3.12+ uyarısı veriyor; datetime.now(timezone.utc) kullanılmalı. Tüm entity'lerde var.
  16. JWT_SECRET_KEY hardcoded fallback
  CLAUDE.md'de not edilmiş; prod'da muhakkak environment'tan alınmalı, fallback tamamen kaldırılmalı.
  17. CORS sabit localhost
  Prod için env-variable tabanlı.
  18. Urun.stok_miktari hesaplanan column_property
  Her sorguda N+1 agregasyon; büyük stokta performans. Materialized view / cache tablosu düşünülebilir.        
  19. TR Zaman Dilimi
  UI'da UTC mi lokal mi gösteriliyor net değil; Europe/Istanbul tutarlılığı doğrulanmalı.
  20. Refresh Token Rotation — Replay Koruması
  Hash tutuluyor (iyi). Ancak "eski refresh token tekrar kullanıldı → tüm oturumları kapat" tespiti var mı?    
  21. Şifre Politikası + MFA
  Min uzunluk, karmaşıklık, brute force kilidi, (opsiyonel) MFA belirgin değil.
  22. Kitting / Bundle / BOM
  Set ürün / paket ürün yok (perakende için sıklıkla gereken).
  23. Mobil Terminal Offline Mod
  mobil_terminal.py router'ı var; offline cache + senkron kuyruk davranışı net değil.

  ---
  ❓ Cevap Beklediğim Sorular

  Planı şekillendirmek için şu noktaları netleştirmek istiyorum:

  1. Sektör odağı: Sistem hangi sektöre konumlandırılıyor? (Gıda/İlaç ⇒ FEFO zorunlu, e-İrsaliye; 3PL ⇒ müşteri
   ayrımı; Perakende ⇒ kitting önemli)
    soru 1 cevap:
     Sistem şu aşamada Türkiye odaklı, tek şirket içi kullanılan genel bir WMS olarak konumlandırılıyor. Ana odağımız mal kabul, yerleştirme, stok yönetimi ve sevkiyat süreçleri. 3PL / multi-tenant yapı ve perakende kitting senaryoları şu an kapsamda değil. Gıda/ilaç gibi sert regülasyonlu bir dikey hedeflemiyoruz; ancak lot/SKT takibi ve gerektiğinde FEFO desteklenebilir olmalı. e-İrsaliye ise önemli bir roadmap maddesi, fakat ilk çekirdek sürüm için zorunlu değil.

  2. Müşteri/Organizasyon modeli: Tek şirket içi mi kullanılacak yoksa multi-tenant (3PL) mı? Tedarikçi var ama
   müşteri entity'si yok — B2B müşteri yönetimi eklenecek mi?
    soru 2 cevap:
    Sistem tek şirket içi kullanım için tasarlanıyor; şu aşamada 3PL / multi-tenant yapı hedeflenmiyor. Bu nedenle tenant bazlı müşteri ayrımı veya çoklu firma mimarisi çekirdek kapsamda değil. Ancak sevkiyat yapılan alıcı firmalar ve B2B ilişkiler için, tenant mantığından bağımsız bir müşteri entity’si ileride operasyonel ihtiyaç doğrultusunda eklenebilir.    

  3. E-İrsaliye (GİB): Zorunlu mu? Entegratör (Logo, Mikro, Uyumsoft vb.) tercihi var mı?
    soru 3 cevap:
    E-İrsaliye önemli bir ihtiyaçtır, ancak ilk çekirdek sürüm için zorunlu değildir; entegrasyon fazında ele alınacaktır. Entegratör tercihi şu an net değildir, bu yüzden yapı sağlayıcıdan bağımsız adapter mantığında tasarlanmalıdır.

  4. ERP: Hangi ERP ile entegrasyon hedefleniyor? ERP = source of truth (memory'de belirtilmiş) —
  ürün/stok/sipariş hangisinin mastersı ERP?
    soru 4 cevap:
    ERP hedef sistemlerden biridir; ancak WMS ana master sistem değil, depo operasyon katmanı olarak konumlandırılmaktadır. Ürün ve sipariş master verilerinin ERP’den gelmesi, WMS’in ise depo içi operasyonları ve stok hareketlerini yönetmesi hedeflenmektedir. ERP tercihi şu aşamada net değildir; yapı adapter tabanlı entegrasyona hazır olmalıdır.

  5. Pick (Toplama) akışı: Sevkiyat hazırlığında palet bazlı mı, koli bazlı mı, adet bazlı mı toplama
  yapılıyor? Şu an SevkiyatKalemi sadece ürün+miktar; hangi paletten toplanacağı atanıyor mu?
    soru 5 cevap:
    Toplama akışı palet bazlı olacaktır. Sevkiyat kalemleri ürün+miktar düzeyinde tanımlansa da, operasyon tarafında bunlar belirli paletlere atanmış Pick Task’lara dönüştürülmelidir. Koli/adet bazlı picking şu an kapsamda değildir.

  6. FEFO zorunluluğu: Sevkiyatta SKT'ye göre otomatik lot seçimi sert kural mı, yoksa operatör ihlal edebilsin
   mi (override log)?
    soru 6 cevap:
    FEFO varsayılan seçim kuralı olmalıdır; ancak bu aşamada mutlak sert kural değil, yetkili kullanıcı için override edilebilir şekilde tasarlanmalıdır. Override işlemleri audit log ile izlenmelidir.

  7. Stok Rezervasyonu: Sipariş "Hazırlanıyor" olduğunda ilgili paletler/lot'lar rezerve edilsin mi
  (rezerve_koli_adedi gibi alan), yoksa fiziksel yükleme anında mı düşülsün?
    soru 7 cevap:
    Rezervasyon, sipariş “Hazırlanıyor” durumuna geçtiğinde başlamalıdır. Paletler bu aşamada siparişe tahsis edilmeli, fiziksel stok düşümü ise sevkiyat kesinleştiğinde yapılmalıdır. İptal veya değişiklikte rezervasyon geri alınabilmelidir.

  8. Cycle Count: ABC sınıflandırma ve döngüsel sayım takvimi önceliğinde mi? (Büyük depo/yüksek SKU adedi     
  varsa şart)
    soru 8 cevap:
    Cycle count önemli bir roadmap maddesidir; ancak ilk çekirdek sürüm için öncelikli değildir. İlk aşamada mevcut stok sayım yapısı yeterlidir; operasyon büyüdükçe ABC bazlı döngüsel sayım planlaması eklenebilir.

  9. Dock/Kapı Randevu: Fiziksel kapı sayısı az ama yoğun mu? Randevu takvimi gerekiyor mu?
    soru 9 cevap:
    Dock/kapı randevu sistemi ilk çekirdek sürüm için öncelikli değildir. Mevcut aşamada temel kapı bilgisi yeterlidir; operasyon yoğunluğu arttığında randevu ve çakışma yönetimi eklenebilir.

  10. Performans / Ölçek: Beklenen SKU adedi, günlük stok hareketi, eşzamanlı operatör sayısı? (Bu concurrency 
  ve slotting kararlarını etkiler)
    soru 10 cevap:
    İlk hedef orta ölçekli depo operasyonlarıdır; çok yüksek hacimli enterprise ölçek şu an birincil varsayım değildir. Sistem birden fazla eşzamanlı operatörü güvenli şekilde desteklemeli ve büyümeye açık olmalıdır; ancak ilk sürüm hiper-ölçek varsayımıyla tasarlanmamalıdır.

  11. Kitting/Bundle: Set/paket ürün var mı?
    soru 11 cevap:
    Kitting / bundle şu an kapsamda değildir. İlk sürümde ürünler bağımsız stok birimleri olarak ele alınacaktır; ihtiyaç oluşursa ileride BOM tabanlı olarak genişletilebilir.

  12. Offline mobil terminal: RF scanner'lar kesintisiz ağa bağlı mı yoksa offline mod gerekli mi?
    soru 12 cevap:
    Offline mobil terminal şu an zorunlu değildir. İlk sürüm online-first çalışacaktır; ancak yapı ileride offline destek eklenebilecek şekilde esnek tasarlanmalıdır.

  13. Öncelik: Yukarıdaki 23 maddeden hangisi canlıya geçiş kritiği sayılıyor, hangisi roadmap'e alınabilir?   
    soru 13 cevap:
    Projenin temel amacı 'Core WMS Engine' (Çekirdek Depo Motoru) yapısının endüstri standartlarında inşa edilmesidir. Bu bağlamda, Faz 1 (Outbound/FEFO/Rezervasyon) ve Faz 2 (Concurrency/Audit/Idempotency) canlıya geçiş için kritik öncelik (MVP - Minimum Viable Product) olarak belirlenmiştir. Bu iki faz tamamlanmadan sistemin güvenilir bir depo yönetimi yaptığı kabul edilmeyecektir.

    Faz 5'teki 'Slotting Optimization', bir AI Mühendisi adayı olarak projeye katacağım teknik imza olması sebebiyle Faz 3'e çekilerek 'Orta Öncelik' grubuna alınmıştır. E-İrsaliye, RMA ve Gelişmiş KPI Dashboard gibi konular ise projenin mimarisi bu genişlemelere hazır tutularak 'Roadmap' (Gelecek Planı) maddesi olarak konumlandırılmıştır.

● Skill(concise-planning)
  ⎿  Successfully loaded skill

● Plan

  Endüstri standardı eksiklikleri 6 faza bölüyorum: kritik (FEFO/Pick/Rezervasyon) → veri bütünlüğü
  (Concurrency/Idempotency/Audit) → işlevsel genişleme (RMA/QC/Cycle Count/Transfer) → entegrasyon
  (e-İrsaliye/ERP) → optimizasyon (Slotting/Dock/KPI) → teknik borç. Cevaplar gelmeden faz sıralaması ve kapsam
   kilitlenmeyecek; her faz öncesi domain → use case → repository → router → test → frontend küçük adım sırası 
  takip edilecek.

  Scope

  - In:
    - 7 kritik eksik (FEFO, Pick Task, Rezervasyon, RMA, QC, Cycle Count, Depo-arası Transfer)
    - 7 orta (e-İrsaliye GİB, Slotting, Dock Randevu, KPI, SKIP LOCKED, Idempotency, Audit immutability)       
    - 9 teknik borç (datetime, JWT secret, CORS, stok cache, TZ, refresh rotation replay, şifre politikası,    
  kitting, offline terminal)
  - Out:
    - Multi-tenant 3PL mimarisi (Soru 2'ye bağlı — dışarıda tutulabilir)
    - UI tema/tasarım yenilemesi
    - Infrastructure/DevOps (CI/CD, k8s) — ayrı bir plan konusu

  Action Items

  Faz 0 — Hazırlık (tüm fazlar öncesi)
  - Kullanıcıdan 13 netleştirme sorusuna cevap al; özellikle 1, 3, 5, 7 blocking
  - datetime.utcnow() → datetime.now(timezone.utc) tüm entity'lerde toplu migrate (quick win)
  - JWT_SECRET_KEY fallback'ini kaldır, startup'ta zorunlu kıl; CORS env-driven yap

  Faz 1 — Kritik: Outbound Doğruluğu (FEFO + Pick + Rezervasyon)
  - ToplamaGorevi (PickTask) domain entity + state machine ekle (Bekliyor→Atandi→DevamEdiyor→Tamamlandi)       
  - PickStrategy servisi: FEFO öncelikli lot/palet seçimi (Lot.son_kullanma_tarihi ASC, fallback FIFO)
  - Sipariş → PickTask generator use case (SevkiyatKalemi'nden palet bazlı görev türetimi)
  - Palet.rezerve_koli_adedi alanı + Lot.rezerve_mi bayrağı; sipariş "Hazırlanıyor" olunca rezerve et,
  iptal/teslimde serbest bırak
  - Rezerve stok hesabını Urun.stok_miktari column_property'sine entegre et (veya uygun_stok ayrı alanı)       
  - FEFO override logging (override_neden alanı) — süpervizör onayı
  - Frontend: ToplamaGorevleriPage (mobil + desktop), pick-confirm akışı
  - Test: FEFO öncelik unit testi, rezervasyon concurrent 2 sipariş integration testi

  Faz 2 — Veri Bütünlüğü (Concurrency + Idempotency + Audit)
  - Repository'de SELECT ... FOR UPDATE SKIP LOCKED ile putaway/pick görev atama (MySQL 8+)
  - Kritik POST uçlarına Idempotency-Key header desteği (middleware + idempotency_keys tablosu)
  - StokHareketi tablosunda UPDATE/DELETE deny — DB trigger veya repository whitelist
  - SistemLog kayıtlarını immutable yap (user_id, action, before/after JSON, hash chain opsiyonel)
  - Refresh token replay koruması: kullanılmış token yeniden sunulursa tüm oturumları kapat
  - Test: 10 eşzamanlı operatör/görev stress testi, idempotency replay testi

  Faz 3 — İşlevsel Genişleme (Müşteri cevaplarına göre sıralanır)
  - İade / RMA: IadeTalebi entity + durum makinesi (Talep→Karantina→QC→Restock/Hurda)
  - QC Workflow: KaliteKontrol entity (numune, test, onay/red), Karantina zonu ile entegrasyon
  - Cycle Count: Urun.abc_sinifi (A/B/C), SayimProgrami entity, scheduler ile otomatik oluşturma
  - Depo-arası Transfer: DepoTransfer entity + transfer irsaliyesi + çift kayıt muhasebesi
  - Kitting/Bundle (Soru 11'e bağlı): UrunBilesimi (BOM) entity
  - Frontend: yukarıdakiler için sayfalar

  Faz 4 — Entegrasyon (Türkiye + ERP)
  - Irsaliye entity'sine GİB alanları: gib_uuid, gib_zarf_id, gib_durum, gib_yanit_kodu
  - GİB entegratör adapter'ı (Soru 3'e göre Logo/Mikro/Uyumsoft)
  - ERP master data sync: ürün/stok/sipariş için ERPSync servisi (tek yönlü, ERP=SoT)
  - E-İrsaliye PDF/XML şablonu + arşivleme
  - Test: GİB sandbox ile uçtan uca gönderim/yanıt

  Faz 5 — Optimizasyon
  - Slotting: Urun.abc_sinifi + raf mesafesi → PutawayStrategy servisi (A sınıfı ön koridorda)
  - Dock Randevu: DockRandevu entity + takvim/çakışma kontrolü, tedarikçi/müşteri self-service
  - KPI formül katmanı: OTIF, Inventory Accuracy, Dock-to-Stock, Pick Accuracy, Order Cycle Time
  - Outbound Dashboard sayfası
  - Urun.stok_miktari için materialized cache tablosu (trigger-based invalidation)

  Faz 6 — Teknik Borç Kapanış
  - TR timezone tutarlılığı (UI her yerde Europe/Istanbul)
  - Şifre politikası (min 10, karmaşıklık, 5 başarısız → 15dk kilit) + opsiyonel TOTP MFA
  - Mobil terminal offline mode (IndexedDB kuyruk + senkron)

  Open Questions (Blocking)

  1. Sektör + e-İrsaliye zorunluluğu (Soru 1, 3): Gıda/İlaç mı? GİB entegrasyonu canlı hedefte mi?
  2. Pick akışı granülaritesi (Soru 5, 6, 7): Palet/koli/adet bazlı toplama? FEFO sert mi override'lı mı?      
  Rezervasyon ne aşamada başlıyor?
  3. Canlıya geçiş kritik öncelik listesi (Soru 13): İlk release için Faz 1 + Faz 2 yeterli mi, yoksa
  e-İrsaliye (Faz 4) eş zamanlı mı?

  ---
  Cevaplarınızı bekliyorum; kritik 3 soruya yanıt verdiğinizde fazları sıralayıp ilk fazın atomik adımlarını   
  kod seviyesine indireceğim.
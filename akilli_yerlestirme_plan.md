Plan — Akıllı Yerleştirme / AI Raf Öneri Modülü                                                             
                                                                                                              
  Mevcut YerlestirmeAlgoritmasi domain servisi (zaten konsolidasyon + doluluk + FIFO + zon önceliği skorlaması   yapan, alternatif raf üreten, mal kabul / belirsiz konum / karantina çıkış akışlarına entegre çalışan)     
  paralel sistem kurmadan genişletilecek. İlk faz; öneriyi standalone (görev oluşturmadan) sorgulayan bir       read-only API ve terminal/depocu UI'da gerekçe + alternatif raflar gösterimi olacak. Kural/skor tabanlı       motor korunur; ML aşaması Faz 3'e ertelenir.                                                                

  ---
  1. CLAUDE.md Kuralları (Özet)
                                                                                                              
  - Backend: Clean Architecture (api → application → core ← infrastructure), Türkçe snake_case, ruff + pyright   (basic, app/).                                                                                               - Router thin; iş mantığı use case + domain service'te. DI factory'leri app/infrastructure/di/modules/
  içine, re-export container.py üzerinden.                                                                      - Repository: abstract (core/repositories) → SQLAlchemy impl (infrastructure/persistence/repositories).
  - Frontend: React 19 + Vite, TypeScript yok (.js/.jsx), TanStack Query (queries/ + queryKeys.js), Tailwind  
  v4, Axios services/api.js.                                                                                    - Test marker'ları: unit | integration | api | concurrency. Backend sonrası ruff check . + pytest -m unit.  
  Frontend sonrası npm run lint.                                                                                - Türkçe isimlendirme şart; alakasız refactor yok; ORM model değişikliğinde Alembic migration zorunlu.
                                                                                                                2. Mevcut Proje Analizi (doğrulanmış)                                                                                                                                                                                       - app/core/services/yerlestirme_algoritmasi.py — raf_oner(palet, urun, depo_id) →                             YerlestirmeOnerisi(onerilen_raf, skor, alternatifler[Top3], gerekce). Skorlama: konsolidasyon %40 + doluluk
  %30 + FIFO/SKT %20 + zon önceliği %10.                                                                      
  - Yardımcı domain servisler: kapasite_dogrulama_servisi.py (slot+ağırlık + alternatif_raflar_getir),
  zon_uyumluluk_servisi.py, fefo_secim_servisi.py.                                                              - Algoritma şu use case'lerde kullanılıyor: mal_kabul_irsaliye_use_cases.py (onayda otomatik öneri → görev),   BilinmeyenKonumGorevleriOlusturUseCase, KarantinadanCikarUseCase. Standalone "öneri sorgula" endpoint'i      yok.
  - Mobil terminal'de zayıf bir adapter var: POST /api/terminal/alternatif-raf — sadece                       
  KapasiteDogrulamaServisi.alternatif_raflar_getir çağırıyor (skor=doluluk, gerekçe yok, ürün/lot bağlamı       yok).
  - DTO'lar: AlternatifRafDTO(raf_id, raf_kod, bos_slot, skor) ve YerlestirmeOnaylaSonucDTO.alternatifler     
  mevcut. gerekce taşıyan DTO yok, frontend'de gerekçe gösterimi yok.                                           - Frontend YerlestirmePage.jsx Adım 3'te gorev.onerilen_raf_kodu'nu gösteriyor; doğrulama hatasında
  sonuc.alternatifler üzerinden override modal'ı çalışıyor — gerekçe ve skor görünmüyor.                        - Test altyapısı: tests/unit/services/test_yerlestirme_algoritmasi.py zaten var (genişletilebilir).
                                                                                                                Eksiklikler: (a) bağımsız "raf öner" sorgu endpoint'i, (b) gerekçe + skor zincirinin DTO/UI'a kadar           taşınması, (c) skor bileşen ayrıştırması (debug/açıklanabilirlik), (d) alternatif raflar için skor (sadece
  alternatif_raflar_getir doluluğa göre sıralıyor — raf_oner ise tam skor üretiyor; iki yol arasındaki farkı  
  tek bir akışta birleştirme).

  3. Modül Konumu                                                                                                
  Mevcut app/core/services/yerlestirme_algoritmasi.py "Akıllı Yerleştirme" motorudur. Yeni paralel servis       kurulmaz. İlk fazda yapılacaklar:
  - Aynı dosyada _skorla çağrısı bileşen sözlüğü döndürecek şekilde küçük genişletme (signature kırmadan).      - Yeni RafOneriSorgulaUseCase (read-only, görev yaratmaz).                                                    - Yeni GET/POST /api/yerlestirme-gorevleri/oneri (veya /api/raflar/oneri) endpoint'i.
  - DTO genişletme: RafOneriResponseDTO, RafOneriDetayDTO (alternatifler için skor + gerekçe).                
  - Mevcut terminal/alternatif-raf endpoint'i deprecate edilmeden kalır; yeni endpoint zenginleştirilmiş      
  veriyi sağlar.                                                                                              
                                                                                                                4. Genişletilecek Mevcut Yapılar                                                                            
                                                                                                                ┌─────────────────────────────┬─────────────────────────────────────────────────────────────────────────┐     │         Mevcut yapı         │                               Genişletme                                │   
  ├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────┤   
  │                             │ İç _skor_bilesenleri(raf, urun, palet) → dict ekle; raf_oner yeni       │ 
  │ YerlestirmeAlgoritmasi      │ opsiyonel palet_no/urun_id/depo_id parametreleriyle çağrılabilen        │ 
  │                             │ yardımcı sarmalayıcı (oneri_sorgula) ekle                               │     ├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────┤ 
  │ YerlestirmeOnerisi          │ bilesenler: dict[str,float] ve alternatif_skorlar: list[(raf, skor,     │   
  │ dataclass                   │ gerekce)] alanları                                                      │     ├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ AlternatifRafDTO            │ İsteğe bağlı gerekce: str | None, skor_bilesenleri: dict | None         │   
  ├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────┤     │ YerlestirmeOnaylaSonucDTO   │ Mevcut alanlara dokunma; alternatifler zenginleşir                      │
  ├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────┤     │ mobil_terminal.py           │ Aynı kalır; yeni endpoint paralel eklenir                               │
  │ /alternatif-raf             │                                                                         │     ├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ depo_envanter_di.py         │ get_raf_oneri_sorgula_uc factory ekle                                   │   
  ├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────┤     │ Frontend                    │ Adım 3'te öneri kartına gerekçe + skor; override modal'da               │
  │ YerlestirmePage.jsx         │ alternatiflerin gerekçesi                                               │     ├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────┤
  │ services/api.js             │ getRafOneri(paletId)                                                    │   
  ├─────────────────────────────┼─────────────────────────────────────────────────────────────────────────┤     │ queries/locationQueries.js  │ useRafOneri(paletId) hook + queryKeys.raflar.oneri(paletId)             │
  └─────────────────────────────┴─────────────────────────────────────────────────────────────────────────┘      
  5. Backend Değişiklikleri (Faz 1)                                                                              
  1. app/core/services/yerlestirme_algoritmasi.py                                                             
    - _skor_bilesenleri() private helper; _skorla bunu çağırır.
    - YerlestirmeOnerisi dataclass'ına bilesenler: dict (ör. {"konsolidasyon":..., "doluluk":..., "fifo":...,   "zon_oncelik":...}) eklenir; default field(default_factory=dict).                                               - raf_oner her alternatif için skor + bileşen + kısa gerekçe taşır (yeni iç tip AlternatifOneri).         
  2. app/application/dto/yerlestirme_gorevi_dto.py                                                            
    - RafOneriDetayDTO(raf_id, raf_kod, zon_kod, skor, bos_slot, gerekce, bilesenler).                        
    - RafOneriResponseDTO(palet_id, palet_no, urun_id, urun_adi, depo_id, onerilen: RafOneriDetayDTO,         
  alternatifler: list[RafOneriDetayDTO], uyari: str | None).                                                      - AlternatifRafDTO'ya opsiyonel gerekce ve bilesenler (geri uyumlu).                                      
  3. app/application/use_cases/yerlestirme_gorevi_use_cases.py                                                
    - RafOneriSorgulaUseCase — palet_id alır, palet+lot+urun+depo'yu çözer, algoritma.raf_oner çağırır, DTO   
  döner. Eksik veri (lot/urun/depo) için GecersizIslemError.                                                    4. app/infrastructure/di/modules/depo_envanter_di.py                                                        
    - get_raf_oneri_sorgula_uc factory + container.py re-export.                                                5. app/api/v1/routers/yerlestirme_gorevleri.py
    - GET /api/yerlestirme-gorevleri/oneri?palet_id=... (admin/depocu/lojistik). Depocu için kullanıcının     
  depo_id'siyle çakışma kontrolü _gorev_depo_yetkisini_dogrula benzeri.                                           - Rate limit 60/minute.                                                                                   
  6. (İsteğe bağlı, Faz 2) mal_kabul_irsaliye_use_cases.py ve BilinmeyenKonumGorevleriOlusturUseCase içinde   
  oneri.bilesenler'i YerlestirmeGorevi üzerinde audit/log alanı olarak persist etmeyi değerlendir (model        değişikliği gerekir).                                                                                       
                                                                                                                Veritabanı / Migration: Faz 1'de gerek yok (yalnızca DTO + read-only). Faz 2'de YerlestirmeGorevi tablosuna   oneri_skoru: float + oneri_gerekcesi: varchar(255) eklenirse Alembic migration gerekir.
                                                                                                                6. Frontend / Terminal Değişiklikleri (Faz 1)                                                                  
  - ReactProje/src/services/api.js: export const getRafOneri = (paletId) =>                                     api.get('/yerlestirme-gorevleri/oneri', { params: { palet_id: paletId } });
  - ReactProje/src/queries/queryKeys.js: yerlestirme.oneri(paletId) key.                                      
  - ReactProje/src/queries/locationQueries.js: useRafOneri(paletId, { enabled }).                             
  - ReactProje/src/pages/terminal/YerlestirmePage.jsx: Adım 3'te öneri kartına gerekce, skor rozetiyle göster;   override modal'da alternatiflerin altına gerekçe satırı.                                                     - ReactProje/src/pages/depocu/... — Mal kabul onay sonrası palet listesinde paletin yanına "Önerilen raf:   
  KOD (skor)" tooltip'i (mevcut bileşeni yeniden kullan; yeni bileşen yaratma).                                  
  Out of scope (Faz 1): Yeni terminal sayfası, ML model entegrasyonu, kullanıcı geri bildirim formu, otomatik   etkileşim öğrenmesi.
                                                                                                              
  7. API Tasarımı 

  GET /api/yerlestirme-gorevleri/oneri?palet_id=123
  → 200 RafOneriResponseDTO                                                                                   
     { palet_id, palet_no, urun_id, urun_adi, depo_id,                                                               onerilen: { raf_id, raf_kod, zon_kod, skor, bos_slot, gerekce, bilesenler },                           
       alternatifler: [ ... aynı şekilde ... ],                                                               
       uyari: null | "Uygun zon bulunamadı" }                                                                 
  → 404 KayitBulunamadi (palet/lot/urun yoksa)                                                                
  → 422 GecersizIslem (depo bağlamı çözülemezse)                                                              
                                                                                                                Mevcut POST /api/terminal/alternatif-raf korunur; yeni endpoint palet bağlamlı zengin öneri için kullanılır.                                                                                                              
  8. Hata Senaryoları                                                                                         

  - Palet yok / pasif → 404.                                                                                    - Palet'in lot/ürün bilgisi yok → 422 "Ürün bilgisi çözülemedi".
  - Depo çözümlenemiyor (raf_id yoksa, mal_kabul_irsaliye yoksa) → 422.                                       
  - Uygun zon yok → uyari alanı dolu, onerilen=null, alternatifler=[], HTTP 200.                              
  - Tüm rafların kapasitesi yetersiz → aynı şekilde 200 + uyari.                                              
  - Kullanıcı depo dışı palet sorguluyor (depocu rolü) → 403 YetkisizIslemError.                              
  - Karantina paleti için → algoritma zaten Karantina zonunu eler; uyari ile bilgilendir.                     
                                                                                                                9. Test Stratejisi                                                                                                                                                                                                        
  - Unit (-m unit):                                                                                           
    - tests/unit/services/test_yerlestirme_algoritmasi.py: _skor_bilesenleri çıktısı (toplam = skor), boş raf,   FIFO sınır durumu (30 günden büyük fark = 0), tüm zonların elenmesi → None, alternatif sıralaması.             - tests/unit/use_cases/test_raf_oneri_sorgula_uc.py (yeni): mock repo ile happy path + eksik lot/urun/depo   + uygun zon yok.                                                                                             - API (-m api): tests/api/routers/test_raf_oneri_endpoint.py — 200/404/422/403 + depocu depo izolasyonu.
  - Integration: Yeni eklemeye gerek yok; mevcut test_putaway_uctan_uce.py rejresyonu için tekrar çalıştır.   
  - Frontend: ESLint çalıştır (npm run lint); manuel terminal akış doğrulaması.                               
                                                                                                                10. Fazlara Bölünmüş Geliştirme Planı                                                                                                                                                                                       - Faz 1 (bu PR) — Read-only öneri API + DTO genişletmesi + algoritma içine bileşen sözlüğü + terminal UI'da   gerekçe/skor gösterimi + unit/api testleri. Migration yok.
  - Faz 2 — YerlestirmeGorevi üstünde oneri_skoru / oneri_gerekcesi / oneri_bilesenleri_json alanları (Alembic   migration), mal kabul + karantina + belirsiz konum akışlarında bu alanları doldurma, raporlamaya ekleme.     - Faz 3 (opsiyonel) — Kullanıcı override veri toplama (görev tamamlandığında öneri vs gerçekleşen raf), bu
  veriyle skor ağırlıklarını depo bazlı ayarlama (yine kural tabanlı, açıklanabilir).                           - Faz 4 (uzun vade) — Geçmiş veri yeterliyse hafif bir öneri modeli (örn. konum-ürün affinitesi); mevcut
  motor "fallback" olarak kalır.                                                                                
  ---                                                                                                         
  Action Items (Faz 1)

  [ ] Discovery — tests/unit/services/test_yerlestirme_algoritmasi.py mevcut test kapsamını gözden geçir,
  eksik kenar durumlarını listele.                                                                              [ ] Algoritma — yerlestirme_algoritmasi.py içinde _skor_bilesenleri ekle, YerlestirmeOnerisi.bilesenler
  alanını ve alternatif skorlarını tutan yardımcı yapıyı genişlet (mevcut raf_oner çağıranları kırmadan).       [ ] DTO — yerlestirme_gorevi_dto.py içine RafOneriDetayDTO ve RafOneriResponseDTO ekle; AlternatifRafDTO'ya
  opsiyonel gerekce/bilesenler ekle.                                                                            [ ] Use Case — RafOneriSorgulaUseCase (palet→lot→urun→depo zinciri + algoritma çağrısı + DTO mapping).
  [ ] DI + Router — depo_envanter_di.py'a get_raf_oneri_sorgula_uc, container.py re-export,                   
  yerlestirme_gorevleri.py router'ına GET /oneri endpoint'i (depocu yetki kontrolü dahil).                      [ ] Test (backend) — Use case için unit test, endpoint için api test (200/404/422/403); ruff check . +      
  pytest -m unit -m api -k "oneri or yerlestirme_algoritmasi" çalıştır.                                         [ ] Frontend API & Query — services/api.js içine getRafOneri, queryKeys.js'e key, locationQueries.js'e
  useRafOneri hook.                                                                                             [ ] Frontend UI — YerlestirmePage.jsx Adım 3'te öneri kartı + skor rozeti + gerekçe; override modal'da
  alternatiflerin gerekçesi; npm run lint.                                                                      [ ] Validation — Terminal akışını manuel doğrula (mal kabul → bekleyen görev → öneri görünümü →
  scan-to-verify hâlâ çalışıyor); rejresyon: pytest -m unit ve pytest                                           tests/integration/test_putaway_uctan_uce.py.
                                                                                                              
  Open Questions  

  - Endpoint kapsamı: önerinin palet_id zorunlu mu, yoksa "irsaliye_id ile toplu öneri" (mal kabul ekranında    listeleme) ihtiyacı var mı? (Faz 1'de tek palet öneririm, toplu öneri Faz 2.)
  - Faz 2'de YerlestirmeGorevi üstüne oneri_skoru/oneri_gerekcesi alanlarını eklemek istiyor musunuz?         
  (Migration gerektirir; Faz 1'i salt okur tutarsak gerekmez.)                                                  - Skor ağırlıkları (40/30/20/10) depo bazlı ayarlanabilir olsun mu? (Şimdilik sabit; Faz 3'e bırakmayı
  öneririm.)
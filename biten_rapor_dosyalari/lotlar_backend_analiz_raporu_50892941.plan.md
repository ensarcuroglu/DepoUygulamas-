---
name: Lotlar Backend Analiz Raporu
overview: "`LotlarPage` ile backend lot yapısı arasındaki akış, sözleşme uyumu ve olası üretim riskleri analiz edildi. Rapor; kritik bulgular, etkileri ve önceliklendirilmiş revizyon önerileri içerir."
todos:
  - id: verify-contract
    content: Lot list/detay response sözleşmesini frontend beklentisiyle netleştir (nested urun/marka veya FE mapping standardı)
    status: pending
  - id: fix-skt-filter
    content: SKT yaklaşan lot sorgusunda SQLAlchemy null filtresini doğrula ve düzelt
    status: pending
  - id: transaction-boundary
    content: Lot CRUD + sistem logu için atomik transaction tasarımı belirle
    status: pending
  - id: paging-filter-design
    content: Sayfalama ve filtreyi server-side veya total-count temelli olarak yeniden tasarla
    status: pending
isProject: false
---

# LotlarPage - Backend Uyum ve Risk Analiz Raporu

## İncelenen Dosyalar
- [ReactProje/src/pages/LotlarPage.jsx](ReactProje/src/pages/LotlarPage.jsx)
- [ReactProje/src/services/api.js](ReactProje/src/services/api.js)
- [BackendProje/app/api/v1/routers/lotlar.py](BackendProje/app/api/v1/routers/lotlar.py)
- [BackendProje/app/application/use_cases/lot_use_cases.py](BackendProje/app/application/use_cases/lot_use_cases.py)
- [BackendProje/app/application/dto/lot_dto.py](BackendProje/app/application/dto/lot_dto.py)
- [BackendProje/app/infrastructure/persistence/repositories/sa_lot_repository.py](BackendProje/app/infrastructure/persistence/repositories/sa_lot_repository.py)
- [BackendProje/models.py](BackendProje/models.py)
- [BackendProje/tests/api/routers/test_lotlar_api.py](BackendProje/tests/api/routers/test_lotlar_api.py)

## Genel Mimari Durum
- Lot backend’i Clean Architecture düzeninde (router -> use_case -> repository) kurgulanmış.
- Frontend `LotlarPage` listeme, SKT yaklaşan listeleme ve pasife alma akışlarını kullanıyor.
- Temel read/write ayrımı (auth/admin) backend’de doğru uygulanmış.

## Kritik Bulgular

### 1) Frontend-backend sözleşme uyuşmazlığı (Yüksek)
- Frontend `lot.urun?.isim` ve `lot.urun?.marka?.id` bekliyor.
- Backend `LotResponseDTO` sadece düz alanlar (`urun_id`, `lot_no`, vb.) döndürüyor; `urun` nested nesnesi yok.
- Etki:
  - Ürün adı çoğunlukla fallback (`Ürün #id`) ile gösterilir.
  - Marka filtresi lot verisinden tutarlı çalışmayabilir.

### 2) SKT yaklaşan sorgusunda SQL koşulu hatalı yazım riski (Yüksek)
- Repository’de `LotORM.son_kullanma_tarihi is not None` ifadesi SQLAlchemy filtresi yerine Python değerlendirmesine kayabilir.
- Beklenen yaklaşım `LotORM.son_kullanma_tarihi.isnot(None)`.
- Etki: SKT yaklaşan listede yanlış/eksik kayıt dönebilir.

### 3) Lot işlemi + sistem logu atomik değil (Orta-Yüksek)
- Lot create/update/delete ve log yazımı ayrı commit akışlarıyla çalışıyor.
- Log yazımı patladığında lot değişikliği kalıcı kalıp log eksik kalabilir.
- Etki: denetim izi bütünlüğü zayıflar.

## Orta Seviye Bulgular

### 4) Sayfalama + client-side filtre çakışması
- İleri butonu `displayLotlar.length < limit` koşuluna bağlı.
- Filtrelenmiş sonuç azaldığında backend’de sonraki sayfa olsa da buton kapanabilir.

### 5) Filtre/arama yalnızca mevcut sayfada
- Arama ve filtreler sadece o an çekilmiş 20 kayıt üzerinde uygulanıyor.
- Kullanıcı tüm lotlar arasında filtre beklerse sonuç yanıltıcı olabilir.

### 6) Marka yükleme hatası sessizce yutuluyor
- `getMarkalar().catch(() => {})` nedeniyle kullanıcı bilgilendirmesi yok.

### 7) İş kuralı validasyonları eksik
- DTO seviyesinde tip/uzunluk kontrolleri var.
- Ancak `uretim_tarihi <= son_kullanma_tarihi` gibi alanlar arası doğrulama yok.

## Frontend’e Geçirilmemiş / Eksik Kullanılan Backend Yapıları

- Frontend servisinde var ama sayfada kullanılmayan lot fonksiyonları:
  - `getLot`, `createLot`, `updateLot`
- Backend’de mevcut ama UI’ye tam taşınmayan yetenekler:
  - `urun_id` query ile server-side filtre
  - Lot soft delete yaşam döngüsü (`aktif=False`) ve buna bağlı iş kuralları
  - CRUD sonrası sistem logları
  - Lot-palet-ürün stok etkileşimi (aktif lot/palet üzerinden stok hesap etkisi)

## Kullanıma Açılmadan Önce Risk Önceliklendirmesi

### P0 (Canlı öncesi mutlaka)
- Lot response sözleşmesini frontend beklentisiyle hizala (nested `urun`/`marka` ya da frontend eşleme stratejisi).
- SKT yaklaşan sorgusundaki `is not None` filtresini SQLAlchemy uyumlu hale getir.

### P1
- Lot işlemi + log yazımını tek transaction sınırına al.
- Pagination/filtre etkileşimini server-side filtreleme veya total-count tabanlı akışa çevir.

### P2
- Marka yükleme hatasını kullanıcıya görünür hale getir.
- Alanlar arası tarih doğrulamalarını use-case katmanına ekle.

## Kısa Sonuç
- Backend temel mimari ve yetkilendirme olarak iyi durumda.
- En büyük sorun, frontend’in beklediği lot veri şekli ile backend DTO dönüşünün uyuşmaması.
- İkinci kritik nokta SKT sorgu filtresi; canlıda yanlış listeleme riski doğurabilir.
- Bu iki alan düzeltilmeden canlıya çıkış, yanlış veri gösterimi ve operasyonel güven kaybı yaratabilir.
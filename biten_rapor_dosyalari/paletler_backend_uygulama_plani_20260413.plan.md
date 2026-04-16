# PaletlerPage Backend Uyum Planı ve Uygulama Kayıtları

## Amaç
`ReactProje/src/pages/PaletlerPage.jsx` ile `BackendProje` palet API davranışını tutarlı hale getirmek, canlı öncesi veri tutarsızlığı ve yarış durumu risklerini kapatmak.

## Kapsam
- Server-side filtreleme entegrasyonu (`lot_id`, `raf_id`, `ean`)
- Infinite scroll + filtre değişimi yarış durumu kontrolü
- Barkod endpoint davranışında aktif/pasif tutarlılığı
- Hata mesajlarının statü koduna göre iyileştirilmesi

## Uygulama Adımları
1. `PaletlerPage` filtre state yapısını backend parametreleriyle uyumlu hale getir.
2. `fetchData` içinde sadece güncel isteğin state yazmasını sağlayan istek sıralama kontrolü ekle.
3. EAN girişini debounce edilmiş ayrı değerle API’ye gönder.
4. Backend barkod endpoint’ine `include_pasif` parametresi ekle (varsayılan: `false`).
5. Frontend hata yönetimini `403/404/429/5xx` senaryoları için netleştir.

## Kabul Kriterleri
- Filtre sonuçları sadece yüklenmiş sayfa değil, backend filtresi ile doğru gelir.
- Hızlı filtre değişiminde eski istekler yeni sonucu ezmez.
- Barkod sonucu pasif kayıtları varsayılan olarak döndürmez.
- Kullanıcıya hata türüne göre anlamlı bildirim gösterilir.

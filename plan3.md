Plan3: Backend Entegrasyon Düzeltmeleri
🚨 Acil (Plan1 İçin)
1. Stok Entegrasyonu
- [ ] update_siparis() → durum "Hazirlaniyor" olunca stok rezervasyonu
- [ ] update_sevkiyat_plani() → durum "Yukleniyor" olunca StokHareketi (cikis) oluştur
- [ ] FIFO mantığı uygula (mevcut crud.py'deki gibi)
2. İrsaliye → Stok Çıkışı
- [ ] create_irsaliye() → otomatik StokHareketi oluştur
- [ ] Çıkış yapılacak miktar = SiparisKalemi toplamı
3. Kapasite Kontrolü
- [ ] Sevkiyat oluştururken Raf.kapasite kontrolü
- [ ] Doluluk % hesapla, uyarı ver
4. İrsaliye PDF Export
- [ ] POST /api/irsaliyeler/{id}/yazdir endpoint
- [ ] Mevcut SevkiyatlarPage.jsxeki HTML şablonunu backend'e taşı
---
🟡 Orta (Plan2 İçin)
5. Rapor Export API
- [ ] POST /api/raporlar/export endpoint
- [ ] type=pdf|excel, sablon_id, tarih_araligi parametreleri
6. Rapor Veri Fonksiyonları
- [ ] get_kritik_stok_raporu() - min_stok altındakiler
- [ ] get_skt_raporu() - SKT'ye < 30 gün kalanlar
- [ ] get_abc_analiz() - ABC kategorizasyonu
7. Rapor Loglama
- [ ] Rapor oluşturulduğunda RaporLogu kaydı yaz
8. Scheduler (Zamanlı Rapor)
- [ ] APScheduler entegrasyonu veya basit cron
- [ ] POST /api/raporlar/schedule/tetikle manual test için
9. E-posta Gönderimi
- [ ] FastAPI-Mail entegrasyonu
- [ ] .env'e SMTP ayarları ekle
- [ ] Scheduler tetiklendiğinde raporu e-posta ile gönder
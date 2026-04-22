# Üretimden Gelen Paletler — İş Akışı Analiz Raporu

Mevcut üretim paleti iş akışını endüstri standartlarıyla karşılaştıran, eksikleri ve iyileştirme önerilerini belirleyen analiz raporu.

---

## 1. Mevcut İş Akışı Haritası

### 1.1. State Machine (Mevcut)

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────┐
│ OLUSTURULDU  │────>│ KABUL_BEKLIYOR   │────>│ KABUL_EDILDI  │
└──────┬───────┘     └───────┬──────────┘     └──┬────────┬───┘
       │                     │                    │        │
       │                     │                    │        ▼
       ▼                     ▼                    │  ┌──────────────┐
┌──────────────┐     ┌──────────────┐            │  │  KARANTINA   │
│ IPTAL_EDILDI │<────│ IPTAL_EDILDI │            │  └──────┬───────┘
└──────────────┘     └──────────────┘            │         │
                                                 │         │(karantina-
                                                 │         │ cikar)
                                                 │         ▼
                                                 │  KABUL_EDILDI
                                                 │  (geri döner)
                                                 ▼
                                          ┌──────────────────────┐
                                          │YERLESTIRME_BEKLIYOR │
                                          └──────────┬───────────┘
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │ YERLESTIRILDI│
                                              └──────────────┘
```

### 1.2. Mevcut Akış Adımları

| Adım | Durum | İşlemci | Açıklama |
|------|-------|---------|----------|
| 1 | `OLUSTURULDU` | Depocu/Admin | Palet oluşturulur, staging rafına atanır, seri no üretilir |
| 2 | `KABUL_BEKLIYOR` | Depocu/Admin | Palet kabul beklemeye alınır |
| 3 | `KABUL_EDILDI` | Depocu/Admin | Palet kabul edilir, stok hareketi (GIRIS) yazılır |
| 4 | `YERLESTIRME_BEKLIYOR` | Depocu/Admin | Yerleştirme için hazır |
| 5 | `YERLESTIRILDI` | Depocu/Admin | Raf atanır, yerleştirme tamamlanır |

### 1.3. Mevcut Veri Modeli

**Palet entity** (`@BackendProje/app/core/entities/palet.py:87-226`):
- Temel: `palet_no`, `lot_id`, `raf_id`, `koli_adedi`, `palet_kg`, `vardiya`
- Üretim meta: `uretim_hatti`, `makine_kodu`, `operator_kullanici_id`, `brut_kg`, `net_kg`
- Kabul audit: `kabul_eden_kullanici_id`, `kabul_tarihi`
- Durum: `kaynak="uretim"`, `durum` (state machine)

**StokHareketi** (`@BackendProje/app/core/entities/stok_hareketi.py:13-51`):
- GIRIS hareketi sadece `KABUL_EDILDI` geçişinde yazılır
- `palet_id`, `palet_no`, `miktar` taşınır

---

## 2. Endüstri Standardı: Üretimden Depoya Giriş Akışı (Dock-to-Stock)

### 2.1. WMS Endüstri Standardı Akış (SAP EWM / Oracle WMS / Blue Yonder referans)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    ÜRETİMDEN DEPOYA (Production Receipt)                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ① ÜRETİM BİLDİRİMİ (Production Notification)                          │
│     Üretim emri tamamlandığında WMS'e "palet hazır" bildirimi           │
│     ─────────────────────────────────────────────────                    │
│     • Üretim emri no / iş emri referansı                                │
│     • Ürün, miktar, lot bilgisi                                         │
│     • Vardiya, hat, makine, operatör                                    │
│     • Beklenen kalite durumu                                            │
│                                                                          │
│  ② DOCK / GEÇİŞ ALANI (Staging / Dock)                                  │
│     Palet fiziksel olarak depo sahasına giriş yapar                     │
│     ─────────────────────────────────────────────────                    │
│     • Barkod/RFID okutma ile tanıma                                     │
│     • Fiziksel sayım doğrulama (beklenen vs gerçek)                    │
│     • Hasar kontrolü (görsel muayene)                                   │
│     • Ağırlık doğrulama (brüt/net tartım)                               │
│                                                                          │
│ ③ KABUL / RECEIVING                                                     │
│     Palet depo envanterine dahil edilir                                 │
│     ─────────────────────────────────────────────────                    │
│     • Stok artışı (GIRIS hareketi)                                      │
│     • Kalite durumu ataması (QI/QC/Blocked)                             │
│     • Son kullanma tarihi kontrolü (FEFO)                               │
│     • Lot traceability kaydı                                            │
│                                                                          │
│ ④ KALİTE KONTROL (QC Hold) — Opsiyonel ama endüstride standart         │
│     Ürün tipine göre zorunlu/opsiyonel QC hold                         │
│     ─────────────────────────────────────────────────                    │
│     • QI (Quality Inspection) durum ataması                             │
│     • Otomatik QC-release kuralı (ürün bazlı)                           │
│     • Manuel QC onay / red akışı                                        │
│     • Örnekleme planı (AQL standardı)                                   │
│                                                                          │
│ ⑤ PUTAWAY (Yerleştirme)                                                 │
│     Palet hedef rafa/konuma yerleştirilir                               │
│     ─────────────────────────────────────────────────                    │
│     • Putaway stratejisi (zon uyumu, FEFO, kapasite)                    │
│     • Sistem önerisi + operatör override                                │
│     • Kapasite & ağırlık kontrolü                                       │
│     • Yerleştirme onayı (konfirmasyon)                                  │
│                                                                          │
│ ⑥ STOKTA (In Stock)                                                     │
│     Palet kullanılabilir stokta                                         │
│     ─────────────────────────────────────────────────                    │
│     • Sevkiyat/toplama için ayrılabilir                                 │
│     • Cycle count kapsamında                                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2. Endüstri Standardı Durum Modeli

| Durum | Açıklama | Stok Etkisi | WMS Karşılığı |
|-------|----------|-------------|---------------|
| **Notified** | Üretim bildirimi alındı, palet henüz fiziksel gelmedi | Yok | SAP: GR Blocked |
| **At Dock** | Palet fiziksel depo alanında, doğrulama bekliyor | Yok | Oracle: Receiving |
| **Received** | Palet kabul edildi, stok artışı yapıldı | +Miktar (Restricted) | SAP: Unrestricted/QI |
| **QC Hold** | Kalite kontrolde, kullanıma kapalı | +Miktar (Blocked) | SAP: Quality |
| **QC Passed** | Kalite onaylı, kullanılabilir | +Miktar (Unrestricted) | Oracle: Available |
| **QC Failed** | Kalite reddedildi | +Miktar (Blocked) | SAP: Blocked |
| **Putaway Ready** | Yerleştirme için hazır | Mevcut | — |
| **Putaway Complete** | Rafta, tam stokta | Mevcut | SAP: Putaway Conf. |
| **Cancelled** | İptal | Yok | — |

---

## 3. Mevcut Akış vs Endüstri Standardı — Gap Analizi

### 3.1. Kritik Eksiklikler

| # | Eksiklik | Mevcut Durum | Endüstri Standardı | Şiddet | Etki |
|---|----------|-------------|-------------------|--------|------|
| **1** | **Üretim Bildirimi (Notification) yok** | Palet doğrudan OLUSTURULDU ile yaratılır | Üretim emri tamamlandığında "palet hazır" bildirimi gelir; WMS bildirimi bekler | 🔴 Yüksek | Üretim-depo koordinasyonu kopuk; palet sahadan kaybolabilir |
| **2** | **Dock/Staging doğrulama yok** | Palet oluşturulurken staging rafına otomatik atanır ama fiziksel doğrulama yapılmaz | Dock'ta barkod okutma + beklenen vs gerçek miktar karşılaştırması + hasar kontrolü | 🔴 Yüksek | Yanlış miktar/hasarlı palet doğrudan stoka girebilir |
| **3** | **Kalite Kontrol (QC Hold) akışı eksik** | KARANTINA var ama: (a) sadece KABUL_EDILDI'dan geçebilir, (b) QC-Pass/Fail ayrımı yok, (c) otomatik QC-release kuralı yok | Ürün bazlı QC zorunluluğu; QI durum; otomatik veya manuel release; AQL örnekleme | 🔴 Yüksek | Gıda/ilaç sınıfı ürünlerde regülasyon riski; kalite güvencesiz stok |
| **4** | **KABUL_BEKLIYOR → KABUL_EDILDI arası otomatik değil** | İki ayrı manuel adım; depocu önce kabul_bekle sonra kabul_et çağırmalı | Barkod okutma ile tek adımda "Receive" (otomatik kabul); sadece özel durumlarda iki adım | 🟡 Orta | Operatör verimlilik kaybı; gereksiz tıklama |
| **5** | **Putaway stratejisi yok** | Yerleştirme tamamen manuel; depocu raf seçer | Zon uyumu + FEFO + kapasite + mesafe bazlı otomatik öneri; override destekli | 🟡 Orta | Yanlış rafa yerleştirme; FEFO ihlali riski |
| **6** | **Yerleştirme onayında raf kapasite kontrolü yok** | `UretimPaletiYerlestirUseCase` raf_id alır ama kapasite/ağırlık kontrolü yapmaz | Hedef rafın kapasite ve ağırlık limiti kontrol edilir; dolu raf reddedilir | 🟡 Orta | Raf aşırı yüklenmesi; fiziksel güvenlik riski |
| **7** | **Brüt/Net tartım doğrulama yok** | `brut_kg` ve `net_kg` alanları var ama doğrulama yapılmıyor | Dock'ta tartım; beklenen vs gerçek ağırlık karşılaştırması; tolerans kontrolü | 🟢 Düşük | Ağırlık tutarsızlığı fark edilmeyebilir |
| **8** | **SKT/FEFO kontrolü kabul anında yok** | SKT lot entity'de var ama kabul akışında kontrol edilmiyor | Geçmiş SKT'li lot otomatik reddedilir veya karantinaya alınır | 🟡 Orta | Geçmiş SKT'li ürün stoka girebilir |

### 3.2. Mevcut Güçlü Yönler

| # | Güçlü Yön | Açıklama |
|---|-----------|----------|
| **1** | State Machine doğru katmanda | `UretimPaletDurum` entity içinde, geçiş kuralları merkezi |
| **2** | Stok hareketi atomik | `KABUL_EDILDI` geçişinde GIRIS hareketi aynı transaction'da |
| **3** | Audit trail var | `PaletDurumLog` her geçişte yazılır; `SistemLog` ek katman |
| **4** | Seri numara üretici | `IUretimSeriNoUretici` portu + atomic sayaç; PRD-YYYYMMDD-NNNN formatı endüstri standardına uygun |
| **5** | Feature flag ile pilot | `_pilot_kontrol` ile kademeli devreye alma |
| **6** | ZPL etiket desteği | Zebra yazıcı ile barkod etiket üretimi mevcut |
| **7** | Karantina temel akışı var | KABUL_EDILDI ↔ KARANTINA geçişi mevcut; yetki kontrolü yapılıyor |
| **8** | Üretim meta alanları mevcut | `uretim_hatti`, `makine_kodu`, `operator_kullanici_id`, `brut_kg`, `net_kg` — izlenebilirlik için yeterli |

---

## 4. Önerilen Hedef İş Akışı

### 4.1. Yeni State Machine

```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│  OLUSTURULDU   │───>│  KABUL_BEKLIYOR│───>│  KABUL_EDILDI  │
│  (Notification) │    │  (At Dock)     │    │  (Received)    │
└───────┬────────┘    └───────┬────────┘    └───┬───────┬────┘
        │                     │                 │       │
        ▼                     ▼                 │       ▼
 ┌──────────────┐     ┌──────────────┐         │  ┌──────────────┐
 │IPTAL_EDILDI  │     │IPTAL_EDILDI  │         │  │  KARANTINA   │
 └──────────────┘     └──────────────┘         │  └──────┬───────┘
                                               │         │
                                               │         ▼
                                               │  ┌──────────────┐
                                               │  │ QC_ONAYLANDI │ ← YENİ
                                               │  └──────┬───────┘
                                               │         │
                                               │  ┌──────┴───────┐
                                               │  │ QC_REDDEDILDI│ ← YENİ
                                               │  └──────┬───────┘
                                               │         │
                                               ▼         ▼
                                        ┌──────────────────────┐
                                        │YERLESTIRME_BEKLIYOR │
                                        └──────────┬───────────┘
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │ YERLESTIRILDI│
                                            └──────────────┘
```

### 4.2. Yeni Durum Tanımları

| Durum | Açıklama | Stok Etkisi | Eklenen Alanlar |
|-------|----------|-------------|-----------------|
| `OLUSTURULDU` | Üretim bildirimi alındı, staging'de | Yok | — |
| `KABUL_BEKLIYOR` | Fiziksel doğrulama bekleniyor | Yok | — |
| `KABUL_EDILDI` | Palet kabul edildi, stok artışı | +Miktar (Restricted) | — |
| `KARANTINA` | QC incelemesinde | +Miktar (Blocked) | `qc_sebep`, `qc_atanan_kullanici_id` |
| `QC_ONAYLANDI` | Kalite onaylı, kullanılabilir | +Miktar (Unrestricted) | `qc_onay_tarihi`, `qc_onay_kullanici_id` |
| `QC_REDDEDILDI` | Kalite reddedildi | +Miktar (Blocked) | `qc_red_sebep`, `qc_red_tarihi` |
| `YERLESTIRME_BEKLIYOR` | Yerleştirme sırası | Mevcut | — |
| `YERLESTIRILDI` | Rafta | Mevcut | — |
| `IPTAL_EDILDI` | İptal | Yok | — |

### 4.3. Kritik İş Kuralları (Eklenmesi Gerekenler)

| # | Kural | Uygulama Yeri | Açıklama |
|---|-------|---------------|----------|
| **K1** | **Ürün bazlı QC zorunluluğu** | `UretimPaletiKabulEtUseCase` | Ürün master'ında `qc_gerekli_mi` flag'i; true ise otomatik KARANTINA'ya al |
| **K2** | **SKT geçmiş kontrolü** | `UretimPaletiKabulEtUseCase` | Lot SKT geçmiş ise otomatik KARANTINA; uyarı ile manuel onay |
| **K3** | **Raf kapasite kontrolü** | `UretimPaletiYerlestirUseCase` | Hedef raf `kapasite_yeterli_mi()` kontrolü; yetersiz ise hata |
| **K4** | **Putaway öneri** | Yeni servis | Zon uyumu + kapasite + FEFO bazlı raf önerisi |
| **K5** | **Hızlı kabul (1-adım)** | `UretimPaletiKabulEtUseCase` | OLUSTURULDU → doğrudan KABUL_EDILDI (KABUL_BEKLIYOR atlanabilir) |
| **K6** | **Tartım doğrulama** | `UretimPaletiKabulEtUseCase` | `brut_kg`/`net_kg` girilmişse beklenen aralıkla karşılaştır |

---

## 5. Detaylı Değişiklik Önerileri

### 5.1. Backend Değişiklikleri

#### A. Entity Değişiklikleri

**`Palet` entity** (`@BackendProje/app/core/entities/palet.py`):

| Değişiklik | Tip | Açıklama |
|------------|-----|----------|
| `qc_sebep: Optional[str]` | Ekle | QC inceleme nedeni |
| `qc_atanan_kullanici_id: Optional[int]` | Ekle | QC'ye atanan kalite personeli |
| `qc_onay_tarihi: Optional[datetime]` | Ekle | QC onay tarihi |
| `qc_onay_kullanici_id: Optional[int]` | Ekle | QC onaylayan |
| `qc_red_sebep: Optional[str]` | Ekle | QC red nedeni |
| `qc_red_tarihi: Optional[datetime]` | Ekle | QC red tarihi |
| `yerlestiren_kullanici_id: Optional[int]` | Ekle | Yerleştiren operatör |
| `yerlestirme_tarihi: Optional[datetime]` | Ekle | Yerleştirme tarihi |

**`UretimPaletDurum` state machine** (`@BackendProje/app/core/entities/palet.py:11-53`):

| Değişiklik | Açıklama |
|------------|----------|
| `QC_ONAYLANDI` durumu ekle | KARANTINA'dan geçiş |
| `QC_REDDEDILDI` durumu ekle | KARANTINA'dan geçiş |
| `KABUL_EDILDI → KARANTINA` geçişi | Mevcut, korunur |
| `KARANTINA → QC_ONAYLANDI` geçişi ekle | QC pass |
| `KARANTINA → QC_REDDEDILDI` geçişi ekle | QC fail |
| `QC_ONAYLANDI → YERLESTIRME_BEKLIYOR` geçişi ekle | Onaylı stok yerleştirilebilir |
| `QC_REDDEDILDI → KARANTINA` geçişi ekle | Ret sonrası tekrar inceleme |
| `OLUSTURULDU → KABUL_EDILDI` geçişi ekle | Hızlı kabul (1-adım) |
| `STOKTA_DURUMLAR` kümesine `QC_ONAYLANDI` ekle | — |
| `KULLANILABILIR_DURUMLAR` kümesine `QC_ONAYLANDI` ekle | — |

**`Urun` entity** (ürün master):

| Değişiklik | Açıklama |
|------------|----------|
| `qc_gerekli_mi: bool = False` ekle | Ürün bazlı QC zorunluluğu flag'i |
| `beklenen_agirlik_kg: Optional[float]` ekle | Tartım doğrulama referansı |
| `agirlik_tolerans_yuzde: Optional[float]` ekle | Tolerans yüzdesi (ör: %5) |

#### B. Use Case Değişiklikleri

| Use Case | Değişiklik | Açıklama |
|----------|------------|----------|
| `UretimPaletiKabulEtUseCase` | SKT kontrolü ekle | `lot.skt_gecmis_mi()` → otomatik KARANTINA |
| `UretimPaletiKabulEtUseCase` | QC zorunluluğu kontrolü ekle | Ürün `qc_gerekli_mi` → otomatik KARANTINA |
| `UretimPaletiKabulEtUseCase` | Hızlı kabul desteği | OLUSTURULDU'dan doğrudan KABUL_EDILDI'ye geçiş |
| `UretimPaletiYerlestirUseCase` | Raf kapasite kontrolü ekle | `raf.kapasite_yeterli_mi()` kontrolü |
| `UretimPaletiYerlestirUseCase` | Yerleştirme audit ekle | `yerlestiren_kullanici_id`, `yerlestirme_tarihi` |
| Yeni: `UretimPaletiQCOnaylaUseCase` | QC onay akışı | KARANTINA → QC_ONAYLANDI |
| Yeni: `UretimPaletiQCReddetUseCase` | QC red akışı | KARANTINA → QC_REDDEDILDI |
| Yeni: `UretimPaletiPutawayOneriUseCase` | Putaway öneri | Zon + kapasite + FEFO bazlı raf önerisi |

#### C. API Değişiklikleri

| Endpoint | Değişiklik |
|----------|------------|
| `POST /{palet_no}/kabul-et` | Hızlı kabul: `OLUSTURULDU` durumunu da kabul etsin |
| `POST /{palet_no}/qc-onayla` | **Yeni** — QC onay |
| `POST /{palet_no}/qc-reddet` | **Yeni** — QC red (sebep zorunlu) |
| `GET /{palet_no}/putaway-oneri` | **Yeni** — Putaway raf önerisi |
| `GET /dashboard/uretim-ozet` | **Yeni** — Dashboard: bekleyen/kabul/karantina/yerleştirilecek sayıları |

#### D. DTO Değişiklikleri

| DTO | Değişiklik |
|-----|------------|
| `UretimPaletiResponseDTO` | `qc_sebep`, `qc_onay_tarihi`, `qc_onay_kullanici_id`, `qc_red_sebep`, `qc_red_tarihi`, `yerlestiren_kullanici_id`, `yerlestirme_tarihi` ekle |
| Yeni: `UretimPaletiQCOnayRequestDTO` | `palet_no`, `sebep` (opsiyonel) |
| Yeni: `UretimPaletiQCRedRequestDTO` | `palet_no`, `sebep` (zorunlu) |
| Yeni: `UretimPaletiPutawayOneriResponseDTO` | `onerilen_raf_id`, `onerilen_raf_kod`, `neden` |

### 5.2. Frontend Değişiklikleri

| Sayfa | Değişiklik |
|-------|------------|
| `UretimPaletiKabulPage` | Hızlı kabul: barkod okutma ile tek adımda OLUSTURULDU → KABUL_EDILDI |
| `UretimPaletleriPage` | QC durumu kolonları; "QC Onayla"/"QC Reddet" butonları |
| Yeni: `UretimPaletiKabulDashboard` | Bekleyen paletler, KPI'lar, hızlı aksiyonlar |
| `DepocuUretimKabulPage` | ScanMonolith + QC bildirimleri + putaway öneri |

---

## 6. Önceliklendirme ve Uygulama Yol Haritası

### Faz A — Kritik Düzeltmeler (1-2 hafta)

| # | Görev | Öncelik | Etki |
|---|-------|---------|------|
| A1 | Hızlı kabul: OLUSTURULDU → KABUL_EDILDI doğrudan geçiş | 🔴 | Operatör verimlilik +50% |
| A2 | Raf kapasite kontrolü (yerleştirme) | 🔴 | Fiziksel güvenlik |
| A3 | SKT geçmiş kontrolü (kabul anında) | 🔴 | Regülasyon riski |
| A4 | Yerleştirme audit alanları | 🟡 | İzlenebilirlik |

### Faz B — Kalite Kontrol Akışı (2-3 hafta)

| # | Görev | Öncelik | Etki |
|---|-------|---------|------|
| B1 | QC_ONAYLANDI / QC_REDDEDILDI durumları | 🔴 | Endüstri standardı uyumu |
| B2 | Ürün bazlı QC zorunluluğu flag'i | 🔴 | Gıda/farma regülasyon |
| B3 | QC onayla/reddet use case + API | 🔴 | Kalite süreci |
| B4 | QC frontend akışları | 🟡 | Operatör deneyimi |

### Faz C — Putaway Optimizasyonu (2-3 hafta)

| # | Görev | Öncelik | Etki |
|---|-------|---------|------|
| C1 | Putaway öneri servisi | 🟡 | Doğru yerleştirme |
| C2 | Zon uyumu + FEFO bazlı öneri | 🟡 | Stok rotasyonu |
| C3 | Putaway öneri API + frontend | 🟡 | Operatör rehberlik |
| C4 | Tartım doğrulama (opsiyonel) | 🟢 | Ağırlık tutarlılığı |

### Faz D — Dashboard ve Raporlama (1-2 hafta)

| # | Görev | Öncelik | Etki |
|---|-------|---------|------|
| D1 | Üretim palet dashboard API | 🟡 | Yönetim görünürlüğü |
| D2 | Inbound dashboard entegrasyonu | 🟡 | Birleşik görünüm |
| D3 | Bekleyen palet bildirimleri | 🟢 | Proaktif yönetim |

---

## 7. Mevcut Akışın Endüstri Standardına Uyumluluk Skoru

| Kategori | Mevcut Skor | Hedef Skor | Gap |
|----------|-------------|------------|-----|
| **İzlenebilirlik (Traceability)** | 7/10 | 9/10 | +2 (QC audit, yerleştirme audit) |
| **Stok Doğruluğu** | 6/10 | 9/10 | +3 (kapasite kontrolü, SKT kontrolü, tartım) |
| **Kalite Güvence** | 3/10 | 8/10 | +5 (QC akışı, ürün bazlı zorunluluk, otomatik hold) |
| **Operatör Verimliliği** | 5/10 | 8/10 | +3 (hızlı kabul, putaway öneri) |
| **Regülasyon Uyumu** | 4/10 | 8/10 | +4 (SKT, QC, audit trail) |
| **Genel** | **5/10** | **8.4/10** | **+3.4** |

---

## 8. Riskler

| Risk | Olasılık | Etki | Azaltma |
|------|----------|------|---------|
| State machine genişlemesi mevcut testleri kırar | Yüksek | Orta | Mevcut testleri önce güncelle, sonra yeni durum ekle |
| QC akışı üretim hattını yavaşlatır | Orta | Yüksek | Ürün bazlı QC; QC gerekmeyen ürünler otomatik geçiş |
| Putaway öneri yanlış raf önerirse | Orta | Orta | Override destekli; öneri = öneri, zorunlu değil |
| Veritabanı şema değişikliği migration gerektirir | Yüksek | Düşük | Nullable alanlar ekle; migration script hazırla |

---

## 9. Sonuç

Mevcut sistem **temel palet kabul akışında sağlam bir altyapıya** sahip: doğru katmanlı mimari, state machine, audit trail ve seri numara üretimi mevcut. Ancak endüstri standardında bir WMS'in üretimden depoya giriş süreci için **3 kritik eksiklik** var:

1. **Kalite kontrol akışı yok** — KARANTINA var ama QC-Pass/Fail ayrımı ve ürün bazlı otomatik QC hold mekanizması eksik
2. **Doğrulama mekanizmaları eksik** — SKT kontrolü, raf kapasite kontrolü, tartım doğrulaması yapılmıyor
3. **Operatör verimliliği düşük** — 2-adım manuel kabul, putaway önerisi yok

Bu 3 alanı kapatmak, sistemi endüstri standardına taşıyacaktır. Faz A ve Faz B'nin tamamlanması ile uyumluluk skoru 5/10'dan 7.5/10'a çıkacaktır.

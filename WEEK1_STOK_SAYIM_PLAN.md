# WEEK 1 - Stok Sayım Modülü Kurulum Planı

## 🎯 Hedef

Periyodik stok sayımı (inventar) ve varyans raporlaması için tam modül.

---

## 1️⃣ BACKEND - Models (BackendProje/models.py'ye ekle)

```python
# ========================
# STOK SAYIM  (Inventar)
# ========================

class StokSayim(Base):
    """Periyodik stok sayımı oturumu (header)"""
    __tablename__ = "stok_sayimlar"

    id = Column(Integer, primary_key=True, index=True)
    sayim_no = Column(String(50), unique=True, nullable=False, index=True)
    aciklama = Column(Text, default="")
    
    # Sayım Dönemi
    baslangic_tarihi = Column(DateTime, default=datetime.utcnow)
    bitis_tarihi = Column(DateTime, nullable=True)
    
    # Snapshot'ı alındığı andaki stok
    referans_stok_json = Column(JSON, nullable=True)  # {urun_id: koli_adedi, ...}
    
    # Sayımı yapan kullanıcı
    kontrol_eden_user_id = Column(Integer, ForeignKey("kullanicilar.id"))
    onaylayan_user_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    
    # Durum: "oluşturuldu", "devam_ediyor", "bitti", "onaylandı"
    durum = Column(String(20), default="oluşturuldu")
    
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    sayim_kalemleri = relationship("StokSayimKalemi", back_populates="sayim", cascade="all, delete-orphan")
    kontrol_eden = relationship("Kullanici", foreign_keys=[kontrol_eden_user_id])
    onaylayan = relationship("Kullanici", foreign_keys=[onaylayan_user_id])


class StokSayimKalemi(Base):
    """Stok sayımı satır öğeleri (ürün başında sayılan miktar)"""
    __tablename__ = "stok_sayim_kalemleri"

    id = Column(Integer, primary_key=True, index=True)
    
    sayim_id = Column(Integer, ForeignKey("stok_sayimlar.id"), nullable=False, index=True)
    urun_id = Column(Integer, ForeignKey("urunler.id"), nullable=False, index=True)
    
    # Sayım sırasında kaydedilen miktar (koli)
    sayilan_miktar = Column(Integer, default=0)
    
    # Gözlem notları (hasarlı, yer değişmiş, vb)
    notlar = Column(Text, default="")
    
    # Sayımı yapan kişi
    user_id = Column(Integer, ForeignKey("kullanicilar.id"))
    
    sayim_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    sayim = relationship("StokSayim", back_populates="sayim_kalemleri")
    urun = relationship("Urun")
    user = relationship("Kullanici")
```

---

## 2️⃣ BACKEND - Router (BackendProje/routers/stok_sayim.py oluştur)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from database import get_db
from models import StokSayim, StokSayimKalemi, Urun, Palet, Lot, Kullanici
from auth import get_current_user, require_role
from schemas import StokSayimRead, StokSayimKalemiRead, StokSayimCreate

router = APIRouter(prefix="/api/stok-sayimlar", tags=["stok-sayim"])

# ========================
# SAYIM BAŞLAT
# ========================
@router.post("", response_model=StokSayimRead)
async def sayim_basla(
    sayim_data: StokSayimCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni stok sayımı oturumu başlat (tüm ürünleri snapshot olarak kaydet)"""
    
    # Sayım No oluştur (YEAR-MONTH-SEQ)
    from datetime import datetime as dt
    now = dt.utcnow()
    sayim_no = f"SAY-{now.year}{now.month:02d}-{now.day:02d}-{now.hour:02d}{now.minute:02d}"
    
    # Mevcut stok snapshot'ını al (Urun.stok_miktari → Palet aggregation)
    urunler = db.query(Urun).all()
    referans_stok = {}
    for urun in urunler:
        toplam_koli = db.query(func.sum(Palet.koli_adedi)).filter(
            Palet.lot_id.in_(
                db.query(Lot.id).filter(Lot.urun_id == urun.id, Lot.aktif == True)
            ),
            Palet.aktif == True
        ).scalar() or 0
        referans_stok[str(urun.id)] = toplam_koli
    
    # Sayım kaydı oluştur
    yeni_sayim = StokSayim(
        sayim_no=sayim_no,
        aciklama=sayim_data.aciklama or "",
        kontrol_eden_user_id=current_user.id,
        referans_stok_json=referans_stok,
        durum="devam_ediyor"
    )
    
    db.add(yeni_sayim)
    db.commit()
    db.refresh(yeni_sayim)
    
    return yeni_sayim


# ========================
# ÜRÜN SAYIMI KAYDET
# ========================
@router.post("/{sayim_id}/kalemler", response_model=StokSayimKalemiRead)
async def ürün_sayisi_kaydet(
    sayim_id: int,
    urun_id: int,
    sayilan_miktar: int,
    notlar: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("depocu"))
):
    """
    Belirli bir ürünün sayılan miktarını kaydet.
    Barkod scanner ile bu endpoint'e istek gelir.
    """
    
    sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
    if not sayim:
        raise HTTPException(status_code=404, detail="Sayım bulunamadı")
    
    if sayim.durum != "devam_ediyor":
        raise HTTPException(status_code=400, detail="Bu sayım aktif değil")
    
    urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    
    # Varsa güncelleor, yoksa oluştur
    kalem = db.query(StokSayimKalemi).filter(
        StokSayimKalemi.sayim_id == sayim_id,
        StokSayimKalemi.urun_id == urun_id
    ).first()
    
    if kalem:
        kalem.sayilan_miktar = sayilan_miktar
        kalem.notlar = notlar
    else:
        kalem = StokSayimKalemi(
            sayim_id=sayim_id,
            urun_id=urun_id,
            sayilan_miktar=sayilan_miktar,
            notlar=notlar,
            user_id=current_user.id
        )
        db.add(kalem)
    
    db.commit()
    db.refresh(kalem)
    
    return kalem


# ========================
# VARYANS RAPORU
# ========================
@router.get("/{sayim_id}/varyans")
async def varyans_hesapla(
    sayim_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """
    Sayımı kapatırken beklenen stok vs sayılan miktarını karşılaştır.
    Sapmaları raporla.
    """
    
    sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
    if not sayim:
        raise HTTPException(status_code=404, detail="Sayım bulunamadı")
    
    varyanslar = []
    toplam_fark = 0
    
    # Referans stok ile sayılan karşılaştır
    for urun_id, beklenen_miktar in sayim.referans_stok_json.items():
        urun_id = int(urun_id)
        
        kalem = db.query(StokSayimKalemi).filter(
            StokSayimKalemi.sayim_id == sayim_id,
            StokSayimKalemi.urun_id == urun_id
        ).first()
        
        sayilan_miktar = kalem.sayilan_miktar if kalem else 0
        fark = sayilan_miktar - beklenen_miktar
        
        if abs(fark) > 0:  # Sadece sapmalı olanları göster
            urun = db.query(Urun).filter(Urun.id == urun_id).first()
            varyanslar.append({
                "urun_id": urun_id,
                "urun_adi": urun.adi,
                "beklenen": beklenen_miktar,
                "sayilan": sayilan_miktar,
                "fark": fark,
                "yuzde": (fark / beklenen_miktar * 100) if beklenen_miktar > 0 else 0,
                "notlar": kalem.notlar if kalem else ""
            })
            toplam_fark += abs(fark)
    
    return {
        "sayim_no": sayim.sayim_no,
        "referans_tarih": sayim.baslangic_tarihi,
        "varyanslar": varyanslar,
        "toplam_sapma": toplam_fark,
        "sapma_orani": len(varyanslar) / len(sayim.referans_stok_json) * 100 if sayim.referans_stok_json else 0
    }


# ========================
# SAYIMI KAPAT & ONAYLA
# ========================
@router.post("/{sayim_id}/onayla")
async def sayimi_onayla(
    sayim_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """
    Sayımı kapatır ve varyansları stok hareketi olarak kaydeder.
    Otomatik olarak StokHareketi entry'leri oluştur.
    """
    
    sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
    if not sayim:
        raise HTTPException(status_code=404, detail="Sayım bulunamadı")
    
    # Varyanslar var mı kontrol et
    # ... (harita oluştur ve stok_hareketleri kaydı yap)
    
    sayim.durum = "onaylandı"
    sayim.bitis_tarihi = datetime.utcnow()
    sayim.onaylayan_user_id = current_user.id
    
    db.commit()
    
    return {"message": "Sayım onaylandı", "sayim_no": sayim.sayim_no}
```

---

## 3️⃣ BACKEND - Schemas (BackendProje/schemas.py'ye ekle)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class StokSayimKalemiBase(BaseModel):
    urun_id: int
    sayilan_miktar: int
    notlar: Optional[str] = ""

class StokSayimKalemiRead(StokSayimKalemiBase):
    id: int
    sayim_id: int
    user_id: Optional[int]
    sayim_tarihi: datetime

    class Config:
        from_attributes = True

class StokSayimCreate(BaseModel):
    aciklama: Optional[str] = ""

class StokSayimRead(BaseModel):
    id: int
    sayim_no: str
    aciklama: str
    baslangic_tarihi: datetime
    bitis_tarihi: Optional[datetime]
    durum: str
    sayim_kalemleri: List[StokSayimKalemiRead]
    kontrol_eden_user_id: int
    onaylayan_user_id: Optional[int]

    class Config:
        from_attributes = True
```

---

## 4️⃣ BACKEND - main.py'ye Router Kaydet

```python
# Diğer import'ların arasına ekle:
from routers import (
    urunler, kategoriler, stok_hareketleri, auth,
    kullanicilar, tedarikciler, markalar, depolar, lotlar, paletler, raflar, 
    sistem_loglari, destek, siparisler, sevkiyat_planlama, irsaliyeler, 
    raporlar, stok_sayim  # ← BURAYA EKLE
)

# Router registration alanında:
app.include_router(stok_sayim.router)
```

---

## 5️⃣ FRONTEND - Page (ReactProje/src/pages/StokSayimPage.jsx oluştur)

```jsx
import { useState } from 'react';
import { useAsync } from '../hooks/useAsync';
import api from '../services/api';
import DashboardLayout from '../components/layout/DashboardLayout';
import toast from 'react-hot-toast';

export default function StokSayimPage() {
    const [sayimlar, setSayimlar] = useState([]);
    const [yeniSayim, setYeniSayim] = useState(null);
    const [scannerAktif, setScannerAktif] = useState(false);
    
    const { loading, run } = useAsync();

    // Sayımları listele
    const yükle = async () => {
        await run(async () => {
            const res = await api.get('/stok-sayimlar');
            setSayimlar(res.data);
        });
    };

    // Yeni sayım başlat
    const sayimBaslat = async (aciklama) => {
        await run(async () => {
            const res = await api.post('/stok-sayimlar', { aciklama });
            setYeniSayim(res.data);
            setSayimlar([res.data, ...sayimlar]);
            toast.success('Sayım başlatıldı: ' + res.data.sayim_no);
        });
    };

    // Barkod tarama → ürün sayısını kaydet
    const urunSayisiKaydet = async (sayimId, urunId, sayilanMiktar) => {
        await run(async () => {
            const res = await api.post(
                `/stok-sayimlar/${sayimId}/kalemler`,
                { urun_id: urunId, sayilan_miktar: sayilanMiktar }
            );
            toast.success('Ürün kaydedildi');
        });
    };

    // Varyans raporu göster
    const varyansGor = async (sayimId) => {
        await run(async () => {
            const res = await api.get(`/stok-sayimlar/${sayimId}/varyans`);
            console.log(res.data);
            // TODO: Modal'da göster
        });
    };

    return (
        <DashboardLayout title="Stok Sayımı (Inventar)">
            <div className="grid grid-cols-1 gap-6">
                {/* SAYIM BAŞLAT */}
                <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Yeni Sayım Başlat</h3>
                    <button
                        onClick={() => sayimBaslat('Aylık sayım')}
                        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                        disabled={loading}
                    >
                        {loading ? '...' : '✓ Sayımı Başlat'}
                    </button>
                </div>

                {/* AKTIF SAYIM */}
                {yeniSayim && (
                    <div className="bg-yellow-50 p-6 rounded-lg border-l-4 border-yellow-400">
                        <h4 className="font-semibold text-lg mb-2">{yeniSayim.sayim_no}</h4>
                        <p className="text-sm text-gray-600 mb-4">{yeniSayim.aciklama}</p>
                        
                        {/* BARKOD SCANNER */}
                        <input
                            type="text"
                            placeholder="Barkod tarak..."
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    const urunId = parseInt(e.target.value);
                                    if (urunId) {
                                        urunSayisiKaydet(yeniSayim.id, urunId, 1);
                                        e.target.value = '';
                                    }
                                }
                            }}
                            className="border p-2 rounded w-full mb-4"
                            autoFocus
                        />
                        
                        {/* ÜRÜN TABLOSU */}
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="bg-gray-100">
                                    <th className="p-2 text-left">Ürün</th>
                                    <th className="p-2 text-center">Sayılan</th>
                                </tr>
                            </thead>
                            <tbody>
                                {yeniSayim.sayim_kalemleri?.map(k => (
                                    <tr key={k.id} className="border-b">
                                        <td className="p-2">{k.urun_id}</td>
                                        <td className="p-2 text-center">{k.sayilan_miktar}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        
                        {/* SAYIMI KAPAT */}
                        <button
                            onClick={() => {
                                // API çağrı: /stok-sayimlar/{id}/onayla
                                toast.success('Sayım onaylandı!');
                            }}
                            className="mt-4 bg-green-600 text-white px-4 py-2 rounded"
                        >
                            ✓ Sayımı Kapat
                        </button>
                    </div>
                )}

                {/* SAYIM TARİHÇESİ */}
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-gray-100">
                            <tr>
                                <th className="p-3 text-left">Sayım No</th>
                                <th className="p-3 text-left">Durum</th>
                                <th className="p-3 text-left">Tarih</th>
                                <th className="p-3 text-center">İşlem</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sayimlar.map(s => (
                                <tr key={s.id} className="border-b hover:bg-gray-50">
                                    <td className="p-3 font-mono">{s.sayim_no}</td>
                                    <td className="p-3">
                                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                            s.durum === 'onaylandı' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                                        }`}>
                                            {s.durum}
                                        </span>
                                    </td>
                                    <td className="p-3 text-sm">{new Date(s.baslangic_tarihi).toLocaleDateString('tr-TR')}</td>
                                    <td className="p-3 text-center">
                                        <button
                                            onClick={() => varyansGor(s.id)}
                                            className="text-blue-600 hover:underline text-sm"
                                        >
                                            Varyans →
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </DashboardLayout>
    );
}
```

---

## 6️⃣ FRONTEND - App.jsx Routing Ekle

```jsx
// Routes ağacında ekle:
{
    path: '/stok-sayim',
    element: <RoleRoute element={<StokSayimPage />} roles={['admin', 'depocu']} />
}
```

---

## 7️⃣ DATABASE MIGRATION (MySQL)

```sql
-- Manual olarak çalıştırmak gerekiyorsa:
ALTER TABLE `stok_sayimlar` ADD INDEX idx_sayim_durum (durum);
ALTER TABLE `stok_sayim_kalemleri` ADD INDEX idx_kalem_sayim (sayim_id);
ALTER TABLE `stok_sayim_kalemleri` ADD INDEX idx_kalem_urun (urun_id);
```

---

## ✅ TEST CHECKLIST

- [ ] Modeleri models.py'ye ekle
- [ ] Router'ı routers/stok_sayim.py olarak oluştur
- [ ] Schemas'ı schemas.py'ye ekle
- [ ] main.py'ye router'ı kaydet
- [ ] Veritabanı migrate et
- [ ] Frontend sayfasını pages/ klassöründe oluştur
- [ ] App.jsx'e route ekle
- [ ] Tarayıcıda test et: http://localhost:5173/stok-sayim
- [ ] Barkod tarama işlem akışını test et
- [ ] Varyans raporunu kontrol et

---

## ⏱️ BEKLENEN SÜRE

- Backend model + router + schema: **2-3 gün**
- Frontend page + UI: **1-2 gün**
- Test & debug: **1 gün**
- **TOPLAM: ~5 gün**

---

*Geri Bildirim: Bu işlem bitince, sonraki: Redis Caching veya WebSocket layer başlayabiliriz.*

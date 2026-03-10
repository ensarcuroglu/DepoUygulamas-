from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Base, Kullanici
from auth import get_current_user, require_role
import crud
from schemas import DashboardStats

# Router'ları içe aktar
from routers import (
    urunler, kategoriler, stok_hareketleri, auth,
    kullanicilar, tedarikciler, markalar, depolar, lotlar, paletler, raflar, sistem_loglari, destek,
    siparisler, sevkiyat_planlama, irsaliyeler
)

# Veritabanı tablolarını oluştur (yoksa)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Depo Yönetim Sistemi API",
    description="Endüstriyel depo ve stok yönetimi için RESTful API — LOT/Palet takibli",
    version="2.0.0"
)

# CORS ayarları — React'ın bu sunucuya erişebilmesi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları kaydet
app.include_router(auth.router)
app.include_router(markalar.router)
app.include_router(urunler.router)
app.include_router(kategoriler.router)
app.include_router(depolar.router)
app.include_router(lotlar.router)
app.include_router(paletler.router)
app.include_router(raflar.router)
app.include_router(stok_hareketleri.router)
app.include_router(kullanicilar.router)
app.include_router(tedarikciler.router)
app.include_router(sistem_loglari.router)
app.include_router(destek.router)
app.include_router(siparisler.router)
app.include_router(sevkiyat_planlama.router)
app.include_router(irsaliyeler.router)


@app.get("/")
def ana_sayfa():
    return {
        "mesaj": "Depo Yönetim Sistemi API'sine hoş geldiniz!",
        "docs": "/docs",
        "versiyon": "2.0.0"
    }


@app.get("/api/dashboard", response_model=DashboardStats)
def dashboard_istatistikleri(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Dashboard için toplam ürün, kritik stok, günlük hareket ve toplam değer istatistikleri"""
    return crud.get_dashboard_stats(db)

# uvicorn main:app --reload --host 127.0.0.1 --port 8000
Uygulama Planı (4 Adım)
Adım 1: Backend Exception System ⏱️ 1 Gün
1.1 Klasör ve Dosyalar Oluştur
BackendProje/
├── core/
│   ├── __init__.py
│   ├── exceptions.py      # ← YENİ
│   └── exception_handlers.py  # ← YENİ
1.2 core/exceptions.py İçeriği
"""
Custom Exception Sınıfları
Tüm API exception'ları bu dosyadan import edilecek
"""
from fastapi import status
from typing import Optional, Any
class APIException(Exception):
    """Base API exception"""
    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
class NotFoundError(APIException):
    """Kaynak bulunamadı hatası (404)"""
    def __init__(self, resource: str, resource_id: int):
        message = f"{resource} (ID: {resource_id}) bulunamadı"
        super().__init__(status.HTTP_404_NOT_FOUND, message, {"resource": resource, "id": resource_id})
class ValidationError(APIException):
    """Giriş validasyonu hatası (422)"""
    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else None
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message, details)
class DuplicateError(APIException):
    """Mükerrer kayıt hatası (409)"""
    def __init__(self, field: str, value: str):
        message = f"{field} '{value}' zaten mevcut"
        super().__init__(status.HTTP_409_CONFLICT, message, {"field": field, "value": value})
class PermissionDeniedError(APIException):
    """Yetki hatası (403)"""
    def __init__(self, message: str = "Bu işlemi yapmaya yetkiniz yok"):
        super().__init__(status.HTTP_403_FORBIDDEN, message)
class AuthenticationError(APIException):
    """Kimlik doğrulama hatası (401)"""
    def __init__(self, message: str = "Kimlik doğrulama başarısız"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, message)
class BadRequestError(APIException):
    """Geçersiz istek hatası (400)"""
    def __init__(self, message: str):
        super().__init__(status.HTTP_400_BAD_REQUEST, message)
1.3 core/exception_handlers.py İçeriği
"""
Global Exception Handler
Tüm custom exception'ları yakalayıp standardize JSON yanıtı döner
"""
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from .exceptions import APIException
async def api_exception_handler(request: Request, exc: APIException):
    """APIException'ları yakalar ve standardize yanıt döner"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "code": exc.status_code,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
async def generic_exception_handler(request: Request, exc: Exception):
    """Beklenmeyen hatalar için fallback handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Sunucu hatası oluştu",
            "code": 500,
            "details": {},
            "timestamp": datetime.utcnow().isoformat()
        }
    )
1.4 core/init.py İçeriği
from .exceptions import (
    APIException,
    NotFoundError,
    ValidationError,
    DuplicateError,
    PermissionDeniedError,
    AuthenticationError,
    BadRequestError,
)
from .exception_handlers import api_exception_handler, generic_exception_handler
__all__ = [
    "APIException",
    "NotFoundError",
    "ValidationError",
    "DuplicateError",
    "PermissionDeniedError",
    "AuthenticationError",
    "BadRequestError",
    "api_exception_handler",
    "generic_exception_handler",
]
1.5 main.py Güncellemesi
# Mevcut importların altına ekle
from core import APIException
from core.exception_handlers import api_exception_handler, generic_exception_handler
# Exception handler'ları kaydet
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
1.6 Router Güncelleme Örnekleri
routers/urunler.py - Önceki:
@router.get("/{urun_id}")
def urun_detay(urun_id: int, db: Session = Depends(get_db)):
    db_urun = crud.get_urun(db, urun_id)
    if not db_urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return db_urun
routers/urunler.py - Sonraki:
from core.exceptions import NotFoundError
@router.get("/{urun_id}")
def urun_detay(urun_id: int, db: Session = Depends(get_db)):
    db_urun = crud.get_urun(db, urun_id)
    if not db_urun:
        raise NotFoundError("Ürün", urun_id)
    return db_urun
routers/lotlar.py - Önceki:
if existing_lot:
    raise HTTPException(status_code=400, detail=f"Bu ürüne ait '{lot.lot_no}' numaralı bir LOT zaten mevcut")
routers/lotlar.py - Sonraki:
from core.exceptions import DuplicateError
if existing_lot:
    raise DuplicateError("LOT numarası", lot.lot_no)
---
Adım 2: Backend Service Layer ⏱️ 2-3 Gün
2.1 Klasör Yapısı
BackendProje/
├── services/
│   ├── __init__.py
│   ├── urun_service.py
│   ├── lot_service.py
│   ├── palet_service.py
│   └── stok_service.py
2.2 services/init.py
from .urun_service import UrunService
from .lot_service import LotService
from .palet_service import PaletService
from .stok_service import StokService
__all__ = ["UrunService", "LotService", "PaletService", "StokService"]
2.3 services/urun_service.py
"""
Ürün İşlemleri Service Layer
CRUD + Business Logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Urun, Lot, Palet
from schemas import UrunCreate, UrunUpdate
from core.exceptions import NotFoundError, DuplicateError, ValidationError
class UrunService:
    """Ürün işlemleri için service layer"""
    
    @staticmethod
    def get_urun(db: Session, urun_id: int) -> Urun:
        """ID'ye göre ürün getir"""
        urun = db.query(Urun).filter(Urun.id == urun_id).first()
        if not urun:
            raise NotFoundError("Ürün", urun_id)
        return urun
    
    @staticmethod
    def get_urun_by_barkod(db: Session, barkod: str) -> Optional[Urun]:
        """Barkod'a göre ürün getir"""
        return db.query(Urun).filter(Urun.barkod == barkod).first()
    
    @staticmethod
    def get_urunler(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        kategori_id: Optional[int] = None,
        marka_id: Optional[int] = None
    ) -> List[Urun]:
        """Ürün listesi getir (filtreleme destekli)"""
        query = db.query(Urun)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Urun.adi.ilike(search_filter)) |
                (Urun.barkod.ilike(search_filter)) |
                (Urun.ean.ilike(search_filter)) |
                (Urun.aciklama.ilike(search_filter))
            )
        
        if kategori_id:
            query = query.filter(Urun.kategori_id == kategori_id)
        
        if marka_id:
            query = query.filter(Urun.marka_id == marka_id)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_kritik_urunler(db: Session) -> List[Urun]:
        """Min stok seviyesinin altındaki ürünleri getir"""
        subquery = db.query(
            Lot.urun_id,
            func.sum(Palet.koli_adedi).label("toplam_stok")
        ).join(Palet, Palet.lot_id == Lot.id).filter(
            Lot.aktif == True,
            Palet.aktif == True
        ).group_by(Lot.urun_id).subquery()
        
        kritikler = db.query(Urun).join(
            subquery, Urun.id == subquery.c.urun_id
        ).filter(
            (Urun.min_stok_seviyesi != None) &
            (subquery.c.toplam_stok < Urun.min_stok_seviyesi)
        ).all()
        
        return kritikler
    
    @staticmethod
    def create_urun(db: Session, urun_data: UrunCreate) -> Urun:
        """Yeni ürün oluştur"""
        # Duplicate kontrolü
        existing = db.query(Urun).filter(Urun.adi == urun_data.adi).first()
        if existing:
            raise DuplicateError("Ürün adı", urun_data.adi)
        
        if urun_data.barkod:
            existing_barkod = db.query(Urun).filter(Urun.barkod == urun_data.barkod).first()
            if existing_barkod:
                raise DuplicateError("Barkod", urun_data.barkod)
        
        urun = Urun(**urun_data.dict())
        db.add(urun)
        db.commit()
        db.refresh(urun)
        return urun
    
    @staticmethod
    def update_urun(db: Session, urun_id: int, urun_data: UrunUpdate) -> Urun:
        """Ürün güncelle"""
        urun = UrunService.get_urun(db, urun_id)
        
        update_data = urun_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(urun, key, value)
        
        db.commit()
        db.refresh(urun)
        return urun
    
    @staticmethod
    def delete_urun(db: Session, urun_id: int) -> bool:
        """Ürün sil (soft delete)"""
        urun = UrunService.get_urun(db, urun_id)
        urun.aktif = False
        db.commit()
        return True
    
    @staticmethod
    def get_urun_stok(db: Session, urun_id: int) -> int:
        """Ürünün toplam stokunu hesapla (FIFO)"""
        toplam = db.query(func.sum(Palet.koli_adedi)).join(
            Lot, Lot.id == Palet.lot_id
        ).filter(
            Lot.urun_id == urun_id,
            Lot.aktif == True,
            Palet.aktif == True
        ).scalar() or 0
        return toplam
2.4 routers/urunler.py Güncelleme
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from auth import get_current_user, require_role
from models import Kullanici
from services.urun_service import UrunService
from schemas import UrunCreate, UrunUpdate, UrunResponse, UrunListResponse
from main import limiter
router = APIRouter(prefix="/api/urunler", tags=["Ürünler"])
@router.get("/", response_model=list[UrunListResponse])
@limiter.limit("100/minute")
def urunleri_listele(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None),
    kategori_id: Optional[int] = Query(None),
    marka_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Tüm ürünleri listeler"""
    return UrunService.get_urunler(db, skip, limit, search, kategori_id, marka_id)
@router.get("/kritik", response_model=list[UrunListResponse])
@limiter.limit("50/minute")
def kritik_urunleri_getir(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Min stok seviyesinin altındaki ürünleri getirir"""
    return UrunService.get_kritik_urunler(db)
@router.get("/barkod/{barkod_kodu}", response_model=UrunResponse)
@limiter.limit("100/minute")
def urun_getir_by_barkod(
    request: Request,
    barkod_kodu: str,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Barkod'a göre ürün getir"""
    db_urun = UrunService.get_urun_by_barkod(db, barkod_kodu)
    if not db_urun:
        from core.exceptions import NotFoundError
        raise NotFoundError("Barkod", barkod_kodu)
    return db_urun
@router.get("/{urun_id}", response_model=UrunResponse)
@limiter.limit("100/minute")
def urun_detay(
    request: Request,
    urun_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Belirli bir ürünün detaylarını getirir"""
    return UrunService.get_urun(db, urun_id)
@router.post("/", response_model=UrunResponse, status_code=201)
@limiter.limit("50/minute")
def urun_ekle(
    request: Request,
    urun: UrunCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni ürün ekle (Admin)"""
    return UrunService.create_urun(db, urun)
@router.put("/{urun_id}", response_model=UrunResponse)
@limiter.limit("50/minute")
def urun_guncelle(
    request: Request,
    urun_id: int,
    urun: UrunUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Ürün güncelle (Admin)"""
    return UrunService.update_urun(db, urun_id, urun)
@router.delete("/{urun_id}")
@limiter.limit("50/minute")
def urun_sil(
    request: Request,
    urun_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Ürün sil (Admin) - Soft delete"""
    UrunService.delete_urun(db, urun_id)
    return {"success": True, "message": "Ürün silindi"}
---
Adım 3: Frontend Error Centralization ⏱️ 1 Gün
3.1 Klasör Yapısı
ReactProje/src/
├── api/
│   ├── __init__.py
│   ├── client.js          # ← api.js'den ayrıştır (axios instance)
│   ├── errors.js          # ← YENİ: Error handling
│   └── endpoints/         # ← YENİ: Endpoint bazlı ayrım
│       ├── __init__.py
│       ├── urunler.js
│       ├── lotlar.js
│       └── ...
3.2 api/errors.js
/**
 * Merkezi Error Handling
 * Backend'den gelen standardize hataları işler
 */
export class ApiError extends Error {
    constructor(message, status, code = null, details = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.code = code;
        this.details = details;
    }
}
export const handleApiError = (error) => {
    // Backend'den gelen standardize response
    if (error.response?.data) {
        const { success, error: message, code, details } = error.response.data;
        
        if (success === false) {
            return new ApiError(message, code, code, details);
        }
    }
    
    // Network hatası
    if (!error.response) {
        return new ApiError('Sunucuya bağlanılamadı', 0, 'NETWORK_ERROR');
    }
    
    // Fallback
    return new ApiError(
        error.response?.data?.detail || 'Beklenmeyen hata oluştu',
        error.response?.status || 500
    );
};
export const forceLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
    }
};
export const isAuthError = (status) => {
    return status === 401 || status === 403;
};
3.3 api/client.js
/**
 * Axios Client
 * Token yönetimi ve interceptors
 */
import axios from 'axios';
import { forceLogout, isAuthError } from './errors';
const API_BASE_URL = 'http://localhost:8000/api';
const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});
// Request interceptor - token ekle
client.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);
// Response interceptor - 401 yönetimi
let isRefreshing = false;
let failedQueue = [];
const processQueue = (error, token = null) => {
    failedQueue.forEach((prom) => {
        if (error) prom.reject(error);
        else prom.resolve(token);
    });
    failedQueue = [];
};
client.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (
            error.response?.status !== 401 ||
            originalRequest._retry ||
            window.location.pathname.includes('/login')
        ) {
            return Promise.reject(error);
        }
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            })
                .then((token) => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return client(originalRequest);
                })
                .catch((err) => Promise.reject(err));
        }
        originalRequest._retry = true;
        isRefreshing = true;
        const refreshToken = localStorage.getItem('refresh_token');
        
        try {
            const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refresh_token: refreshToken
            });
            
            const { access_token } = res.data;
            localStorage.setItem('access_token', access_token);
            
            processQueue(null, access_token);
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            
            return client(originalRequest);
        } catch (refreshError) {
            processQueue(refreshError, null);
            forceLogout();
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);
export default client;
3.4 api/endpoints/urunler.js
/**
 * Ürün Endpoint'leri
 */
import client from '../client';
import { handleApiError } from '../errors';
export const urunlerApi = {
    getAll: async (params = {}) => {
        try {
            const response = await client.get('/urunler/', { params });
            return response.data;
        } catch (error) {
            throw handleApiError(error);
        }
    },
    getById: async (id) => {
        try {
            const response = await client.get(`/urunler/${id}`);
            return response.data;
        } catch (error) {
            throw handleApiError(error);
        }
    },
    getByBarkod: async (barkod) => {
        try {
            const response = await client.get(`/urunler/barkod/${barkod}`);
            return response.data;
        } catch (error) {
            throw handleApiError(error);
        }
    },
    create: async (data) => {
        try {
            const response = await client.post('/urunler/', data);
            return response.data;
        } catch (error) {
            throw handleApiError(error);
        }
    },
    update: async (id, data) => {
        try {
            const response = await client.put(`/urunler/${id}`, data);
            return response.data;
        } catch (error) {
            throw handleApiError(error);
        }
    },
    delete: async (id) => {
        try {
            const response = await client.delete(`/urunler/${id}`);
            return response.data;
        } catch (error) {
            throw handleApiError(error);
        }
    },
};
3.5 api/init.py
export { default as client } from './client';
export { handleApiError, forceLogout, ApiError, isAuthError } from './errors';
export { urunlerApi } from './endpoints/urunler';
---
Adım 4: Klasör Organizasyonu (Opsiyonel) ⏱️ 1 Gün
Bu adım mevcut yapıyı bozmadan daha temiz bir organizasyon sağlar. İlerleyen aşamalarda yapılabilir.
BackendProje/
├── database/
│   ├── __init__.py
│   └── db.py           # ← database.py'den ayrıştır
├── schemas/
│   ├── __init__.py
│   ├── request.py      # ← ayrıştır
│   └── response.py     # ← ayrıştır
ReactProje/src/
├── components/
│   ├── common/         # ← Button, Input, Modal, vb.
│   ├── forms/          # ← Form bileşenleri
│   └── tables/         # ← Tablo bileşenleri
---
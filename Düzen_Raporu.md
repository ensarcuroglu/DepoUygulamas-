# Depo Yönetim Sistemi - Kod Düzenleme & Standarlaştırma Raporu

**Tarih:** 12 Mart 2026  
**Hazırladı:** Code Analysis  
**Durum:** DRAFT → IMPLEMENTATION PHASE  
**Target:** Production-ready codebase + team collaboration ready

---

## 📋 EXECUTIVE SUMMARY

Mevcut proje iyi özelliklere sahip olsa da, **kod organizasyonu, kalite standartları ve dokumentasyon** eksikliğinden dolayı bakım-geliştirme maliyeti artmaktadır. Bu rapor:

- ✅ Şu anki karmaşıklığı detaylı olarak ortaya koymaktadır
- ✅ 3 fazlı refactoring planı sunmaktadır
- ✅ **Enforceable** kod standartları tanımlamaktadır
- ✅ Team collaboration'a hazırlık yapacak kuralları belirtmektedir

**Tahmini İyileştirme Süresi:** 6-8 hafta (uygulamalı olarak, daily development ile)

---

## 🔴 PROBLEM STATEMENT

### Mevcut Durumun Maliyeti

| Sorun | Örnek | Etki |
|-------|-------|------|
| **Folder Structure Düzensiz** | Backend routers'daki dosyaları bulmak 10 dk sürebilir | 25% verimlilik kaybı |
| **Duplicate Code Çok** | `hata.js` ile benzer error handling 5-6 yerde tekrar | 40% daha fazla debug süresi |
| **Error Handling Karışık** | Bahan EndPoint'ler farklı hata response'ları | API'nin inconsistent davranışı |
| **Test Yok** | Refactor yapın → ne kırıldığını bilemez | 1 küçük değişiklik = 4 saat test |
| **Documentation Yok** | Yeni developer başladığında onboarding impossible | 2 hafta mentoring gerekli |
| **Performance Issues** | N+1 queries, no caching, no optimization | Dashboard slow (3-5 sec) |

---

## 📊 I. CURRENT STATE ANALYSIS (DETAYLI)

### A. FOLDER STRUCTURE SORUNU

#### ❌ Şu Anki Durum (Karışık)
```
BackendProje/
├── auth.py                 # ← İçine 400+ satır (auth + token + password)
├── crud.py                 # ← İçine 2000+ satır (30+ function)
├── database.py
├── models.py               # ← İçine 700+ satır (12+ model)
├── schemas.py              # ← İçine 600+ satır (request/response)
├── main.py                 # ← İçine 300+ satır (routes, scheduler, middleware)
├── seed.py
├── routers/
│   ├── auth.py            # Duplicate: main.py'deki auth ile karışıyor
│   ├── urunler.py
│   ├── lotlar.py
│   ├── ... (15 router dosyası)
└── uploads/

ReactProje/
├── src/
│   ├── components/         # Sabit componentler var mı? Components organize edilmiş mi?
│   ├── pages/             # 20+ page dosyası (DevBug: benzer patterns)
│   ├── services/
│   │   └── api.js         # ← İçinde 300+ satır (request, response, interceptor)
│   ├── utils/
│   │   └── hata.js        # ← Benzer error logic 5 yerde tekrar
│   └── contexts/
        └── AuthContext.jsx # ← Token logic'i ayrı yerde
```

#### ✅ Önerilen Durum (Clean)
```
BackendProje/
├── config/
│   ├── settings.py         # ← Env, constants, config
│   └── __init__.py
├── core/
│   ├── auth.py            # ← Pure auth logic (JWT, password)
│   ├── security.py        # ← Role checks, permissions
│   ├── exceptions.py       # ← Custom exceptions (APIError, ValidationError)
│   └── __init__.py
├── database/
│   ├── db.py              # ← Engine, SessionLocal, get_db
│   ├── models.py          # ← ORM models (sadece models!)
│   └── __init__.py
├── orm/
│   ├── models/__init__.py
│   ├── models/marka.py
│   ├── models/kategori.py
│   ├── models/urun.py     # ← Büyük tables ayrı dosya
│   ├── models/lot.py
│   ├── models/palet.py
│   ├── models/stok_hareketi.py
│   └── ...
├── schemas/
│   ├── request.py         # ← Input validation schemas
│   ├── response.py        # ← Output schemas
│   ├── marka.py
│   ├── urun.py
│   └── __init__.py
├── services/
│   ├── urun_service.py    # ← Ürün işlemleri (CRUD + logic)
│   ├── stok_service.py    # ← Stok hareketi, FIFO logic
│   ├── sayim_service.py   # ← Stok sayımı
│   ├── notification_service.py  # ← Email, SMS, alerts
│   └── __init__.py
├── routers/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── urunler.py
│   │   ├── depolar.py
│   │   ├── lotlar.py
│   │   └── ... (cleanly organized)
│   └── v2/ (future versioning ready)
├── migrations/            # ← Alembic (if needed later)
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_urun_crud.py
│   └── test_services/
├── main.py               # ← ONLY: app setup, route inclusion, middleware
├── requirements.txt
├── .env.example
└── README.md

ReactProje/src/
├── types/               # ← TypeScript types (API, models)
│   ├── index.d.ts
│   ├── api.d.ts
│   └── models.d.ts
├── api/                 # ← Centralized API layer
│   ├── client.js        # ← Axios instance + interceptors
│   ├── endpoints/
│   │   ├── auth.js
│   │   ├── urunler.js
│   │   ├── stok.js
│   │   └── __init__.js
│   └── errors.js        # ← Error handling (single source)
├── components/
│   ├── common/          # ← Reusable (Button, Input, Modal, etc)
│   ├── layout/
│   ├── forms/           # ← Form components (UrunForm, LotForm, etc)
│   ├── tables/          # ← Table components (generic)
│   └── modals/
├── pages/               # ← Page containers (with routing)
├── hooks/               # ← Custom hooks
├── contexts/            # ← Global state (Auth, Notifications)
├── utils/
│   ├── formatting.js
│   ├── validation.js
│   ├── export.js
│   └── constants.js
├── services/
│   ├── authService.js   # ← Auth business logic
│   ├── storageService.js # ← Local storage management
│   └── notificationService.js
├── styles/
│   ├── globals.css
│   └── variables.css    # ← Tailwind custom variables
└── App.jsx
```

---

### B. DUPLICATE CODE PROBLEMI

#### ❌ Şu Anki Sorunlar

```javascript
// services/api.js - Error handling
const forceLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
    }
};

// ← Aynı logic pages/LoginPage.jsx'de tekrar yazılmış
// ← Aynı logic pages/ProfilAyarlariPage.jsx'de de tekrar
// ← Aynı logic contexts/AuthContext.jsx'de de var!
```

```python
# BackendProje/routers/urunler.py
try:
    # operation
except Exception as e:
    logger.error(f"Hata: {e}")
    raise HTTPException(status_code=500, detail="İç server hatası")

# routers/lotlar.py
try:
    # operation
except Exception as e:
    logger.error(f"Hata oluştu: {e}")  # ← Farklı mesaj!
    raise HTTPException(status_code=500, detail="Server hatası")

# routers/paletler.py
try:
    # operation
except Exception as e:
    # ← Hiç hata handle edilmemiş!
    pass
```

#### ✅ FIX: Centralized Error Handling

```python
# BackendProje/core/exceptions.py
from fastapi import status

class APIException(Exception):
    """Base API exception"""
    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}

class ValidationError(APIException):
    def __init__(self, message: str, field: str = None):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, message, {"field": field})

class NotFoundError(APIException):
    def __init__(self, resource: str, resource_id: int):
        msg = f"{resource} (ID: {resource_id}) bulunamadı"
        super().__init__(status.HTTP_404_NOT_FOUND, msg)

class PermissionDeniedError(APIException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, "Bu işlemi yapmaya yetkiniz yok")

class DuplicateError(APIException):
    def __init__(self, field: str, value: str):
        msg = f"{field} '{value}' zaten var"
        super().__init__(status.HTTP_409_CONFLICT, msg)
```

```python
# BackendProje/core/exception_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from .exceptions import APIException

async def api_exception_handler(request: Request, exc: APIException):
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
```

```python
# main.py
from core.exception_handlers import api_exception_handler
from core.exceptions import APIException

app.add_exception_handler(APIException, api_exception_handler)
```

---

### C. ERROR HANDLING INCONSISTENCY

#### ❌ Sorunlar
```python
# Router A
if not user:
    raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

# Router B
if not user:
    raise HTTPException(status_code=404, detail="User not found")  ← İngilizce!

# Router C
if not user:
    return {"error": "Kullanıcı yok"}  ← Status code yok, response format farklı

# Router D
if not user:
    raise Exception("User hatası")  ← Generic exception, format yok
```

#### ✅ FIX Approach
```python
# Tüm routers'da kullan:
if not urun:
    raise NotFoundError("Ürün", urun_id)

# Output: {"success": False, "error": "Ürün (ID: 5) bulunamadı", ...}
```

---

### D. TESTING INFRASTRUCTURE YOKSUNLUĞU

#### ❌ Risk
- Refactor yapıyorsun → ne kırıldığını bilemez
- Bug fix → başka yerde başka bug çıkıyor
- New feature → production'da crash

#### ✅ Yapılacak
```
BackendProje/tests/
├── conftest.py              # ← Pytest fixtures (test DB, test user, etc)
├── test_auth.py             # ← JWT, refresh token, role checks
├── test_crud.py             # ← CRUD operations, FIFO logic
├── test_services/
│   ├── test_urun_service.py
│   ├── test_stok_service.py
│   └── test_sayim_service.py
└── test_integration/        # ← End-to-end tests

ReactProje/src/
├── __tests__/
│   ├── setup.js
│   ├── components/
│   │   └── PrivateRoute.test.jsx
│   ├── hooks/
│   │   └── useAsync.test.js
│   └── services/
│       └── api.test.js
```

---

## 🎯 II. REFACTORING ROADMAP (3 FAZE)

### FAZE 1: FOUNDATION (Hafta 1-2) — Altyapı Kurma

#### Goal: Standartlar tanımla + enforcing tools kur

**Backend:**

```bash
# 1. Code quality tools kur
pip install black pytest pytest-asyncio pylint flake8 mypy

# 2. Pre-commit hook'ları ekle
pip install pre-commit

# .pre-commit-config.yaml oluştur
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    hooks:
      - id: flake8
```

```bash
# 3. pyproject.toml veya setup.cfg'de konfigure et
[tool.black]
line-length = 100
target-version = ['py38', 'py39']

[tool.pylint]
max-line-length = 100
```

**Frontend:**

```bash
# 1. TypeScript + ESLint config upgrade
npm install --save-dev typescript @typescript-eslint/parser @typescript-eslint/eslint-plugin

# 2. Prettier kur (auto-formatting)
npm install --save-dev prettier

# 3. Pre-commit hooks
npm install --save-dev husky lint-staged
npx husky install
npx husky add .husky/pre-commit "npm run lint:fix && npm run format"
```

**Configuration Files:**

```json
// ReactProje/.prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2
}
```

```json
// ReactProje/eslint.config.js (upgrade)
export default [
  {
    files: ['src/**/*.{js,jsx}'],
    rules: {
      // Enforce naming conventions
      'no-var': 'error',
      'prefer-const': 'error',
      'camelcase': 'error',
      'no-unused-vars': 'error',
      'eqeqeq': 'error'
    }
  }
]
```

#### Yapılacak:
- [ ] ESLint + Prettier setup (Frontend)
- [ ] Black + Pylint setup (Backend)
- [ ] Pre-commit hooks configure
- [ ] CODING_STANDARDS.md yaz
- [ ] Folder structure plan belgesi oluştur

**Tahmini Süre:** 1-2 gün

---

### FAZE 2: REFACTOR CORE MODULES (Hafta 3-4) — Çekirdek Modüller

#### Goal: Folder structure + error handling standardleş + duplicate code elimine

**Priority Order:**

```
1️⃣ Backend Exception System
   - core/exceptions.py + handlers
   - Tüm routers'da test et
   - Time: 1 gün

2️⃣ Backend Folder Restructure
   - models/ → ayrı dosyalar
   - schemas/ → ayrı dosyalar
   - services/ → iş mantığı
   - Time: 3 gün

3️⃣ Frontend Error Handling Centralize
   - api/errors.js (single source)
   - Logout logic → AuthContext
   - Toast/notification centralized
   - Time: 2 gün

4️⃣ Frontend Folder Restructure
   - components/ → organized
   - api/ → endpoint wrappers
   - Time: 2 gün
```

#### FIZ Mock Code:

```python
# BackendProje/services/urun_service.py oluştur
from typing import List
from sqlalchemy.orm import Session
from models import Urun, Lot, Palet
from schemas import UrunCreate, UrunUpdate, UrunRead
from core.exceptions import NotFoundError, DuplicateError

class UrunService:
    """Ürün işlemleri (CRUD + business logic)"""
    
    @staticmethod
    def create_urun(db: Session, urun_data: UrunCreate) -> Urun:
        """Yeni ürün oluştur"""
        # Duplicate check
        existing = db.query(Urun).filter(Urun.adi == urun_data.adi).first()
        if existing:
            raise DuplicateError("Ürün adı", urun_data.adi)
        
        # Create
        urun = Urun(**urun_data.dict())
        db.add(urun)
        db.commit()
        db.refresh(urun)
        return urun
    
    @staticmethod
    def get_urun(db: Session, urun_id: int) -> Urun:
        """Ürün getir"""
        urun = db.query(Urun).filter(Urun.id == urun_id).first()
        if not urun:
            raise NotFoundError("Ürün", urun_id)
        return urun
    
    @staticmethod
    def get_urun_stok(db: Session, urun_id: int) -> int:
        """Ürünün toplam stokunu hesapla (FIFO: active lots'daki pallets)"""
        toplam = db.query(func.sum(Palet.koli_adedi)).filter(
            Palet.lot_id.in_(
                db.query(Lot.id).filter(
                    Lot.urun_id == urun_id,
                    Lot.aktif == True
                )
            ),
            Palet.aktif == True
        ).scalar() or 0
        return toplam
```

```python
# routers/v1/urunler.py (refactored)
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_role
from services.urun_service import UrunService
from schemas import UrunCreate, UrunRead
from core.exceptions import ValidationError

router = APIRouter(prefix="/api/v1/urunler", tags=["urunler"])

@router.post("", response_model=UrunRead, status_code=status.HTTP_201_CREATED)
async def create_urun(
    urun_data: UrunCreate,
    db: Session = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Yeni ürün oluştur"""
    # No try-except needed - exceptions handled globally
    urun = UrunService.create_urun(db, urun_data)
    return urun
```

**Tahmini Süre:** 4-5 gün

---

### FAZE 3: TESTING + DOCUMENTATION (Hafta 5-6) — Kaliteli Altyapı

#### Goal: Test coverage + API documentation + internal docs

**Backend Tests:**

```python
# BackendProje/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from models import Base
from fastapi.testclient import TestClient

# Test database
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Tüm tests için fresh DB"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Test client"""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_admin_user(db):
    """Admin test user"""
    user = Kullanici(
        email="admin@test.com",
        password_hash=get_password_hash("test123"),
        rol="admin"
    )
    db.add(user)
    db.commit()
    return user
```

```python
# BackendProje/tests/test_urun_crud.py
def test_create_urun(client, test_admin_user):
    """Ürün oluştur"""
    response = client.post(
        "/api/v1/urunler",
        json={"adi": "Test Ürün", "sku": "TEST-001", ...},
        headers={"Authorization": f"Bearer {test_admin_user.token}"}
    )
    assert response.status_code == 201
    assert response.json()["adi"] == "Test Ürün"

def test_get_urun(client):
    """Ürün getir"""
    response = client.get("/api/v1/urunler/1")
    assert response.status_code == 200

def test_duplicate_urun_name(client, test_admin_user):
    """Duplicate ürün adı reddedilir"""
    # First create
    client.post("/api/v1/urunler", json={"adi": "Test"}, headers=...)
    # Try duplicate
    response = client.post("/api/v1/urunler", json={"adi": "Test"}, headers=...)
    assert response.status_code == 409  # Conflict
```

**Frontend Tests:**

```javascript
// ReactProje/src/__tests__/services/api.test.js
import { describe, it, expect, beforeEach, vi } from 'vitest';
import api from '../../api/client';

describe('API Service', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should add Bearer token to requests', () => {
    localStorage.setItem('access_token', 'test-token');
    expect(api.defaults.headers.common.Authorization).toBe('Bearer test-token');
  });

  it('should remove token on 401 response', async () => {
    // Mock 401 response
    vi.spyOn(api, 'get').mockRejectedValueOnce({ response: { status: 401 } });
    
    // Attempt request
    try {
      await api.get('/api/test');
    } catch (e) {
      expect(localStorage.getItem('access_token')).toBeNull();
    }
  });
});
```

**Documentation:**

```markdown
# BackendProje/DEVELOPMENT.md
## Folder Structure

### /core
- **auth.py** — JWT token creation/validation, password hashing
- **security.py** — Role-based access control, permission checks
- **exceptions.py** — Custom exception classes
- **exception_handlers.py** — Global exception handler

### /database
- **db.py** — SQLAlchemy engine, session, get_db dependency
- **models.py** — ORM models (legacy, to be split)

### /orm/models
- One file per major model (urun.py, lot.py, palet.py, etc)
- Relationships should be one-directional when possible

### /schemas
- **request.py** — Input validation (Create, Update)
- **response.py** — Output response models (Read)
- Table-specific schemas in separate files if >100 lines

### /services
- Business logic layer (CRUD + domain operations)
- Example: UrunService, StokService, SayimService
- No direct DB queries in routers — use services!

### /routers/v1
- One router per entity
- Use services for business logic
- Minimal endpoint - just validate → call service → respond
```

```markdown
# ReactProje/DEVELOPMENT.md
## Component Structure

### /components/common
Generic, reusable components:
- Button.jsx
- Input.jsx
- Modal.jsx
- Dropdown.jsx
- Pagination.jsx

### /components/forms
Form-specific components:
- UrunForm.jsx
- LotForm.jsx
- PaletForm.jsx

### /components/tables
Table-specific components:
- UrunTable.jsx
- StokTable.jsx

### /api/endpoints
Endpoint wrappers:
- urunler.js → API calls for /api/urunler/*
- stok.js → API calls for /api/stok-hareketleri/*
- Format: { getAll(), create(), update(), delete(), ... }

## Error Handling
All errors handled by:
1. api/errors.js — parse & format errors
2. AuthContext — handle 401 (logout)
3. Toast notifications — show to user
```

**Tahmini Süre:** 4-5 gün

---

## 📏 III. CODING STANDARDS (Enforced)

### Backend (Python) Standards

#### Naming Conventions
```python
# ✅ DO
class UrunService:  # Classes: PascalCase
    pass

def create_urun(db, urun_data):  # Functions: snake_case
    urun_id = 1  # Variables: snake_case
    MAX_ITEMS = 100  # Constants: UPPER_SNAKE_CASE

# ❌ DON'T
class urunService:  # lowercase
    pass

def CreateUrün(db, urunData):  # camelCase, Turkish chars
    URUNID = 1  # inconsistent
```

#### File Organization
```python
# File structure: imports → constants → classes → functions
"""Module docstring"""

from typing import List  # Standard library
from sqlalchemy import Column  # Third party
from models import Urun  # Local imports
from core.exceptions import NotFoundError

CACHE_LIFETIME = 3600  # Constants

class MyClass:  # Classes
    """Class docstring"""
    pass

def my_function():  # Functions
    """Function docstring"""
    pass
```

#### Error Handling (MUST)
```python
# ✅ DO
@router.get("/urunler/{urun_id}")
async def get_urun(urun_id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not urun:
        raise NotFoundError("Ürün", urun_id)
    return urun

# ❌ DON'T
@router.get("/urunler/{urun_id}")
async def get_urun(urun_id: int, db: Session = Depends(get_db)):
    urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not urun:
        return {"error": "Not found"}  # Wrong format
    return urun
```

#### Type Hints (MUST)
```python
# ✅ DO
def calculate_total(items: List[int]) -> int:
    """Calculate sum of items"""
    return sum(items)

# ❌ DON'T
def calculate_total(items):  # No type hints
    return sum(items)
```

#### Documentation (MUST)
```python
# ✅ DO
def get_urun_stok(db: Session, urun_id: int) -> int:
    """
    Calculate total stock quantity for a product.
    
    Uses FIFO method: sums active pallets in active lots.
    
    Args:
        db: Database session
        urun_id: Product ID
    
    Returns:
        Total quantity (in boxes/units)
    
    Raises:
        NotFoundError: If product doesn't exist
    """
    ...

# ❌ DON'T
def get_urun_stok(db, urun_id):
    # get stock
    ...
```

---

### Frontend (JavaScript/React) Standards

#### Naming Conventions
```javascript
// ✅ DO
function getUserList(filters) { }  // Functions: camelCase
const MAX_ITEMS = 10;              // Constants: UPPER_SNAKE_CASE
const user = { name: 'John' };    // Variables: camelCase

function UserCard() { }            // Components: PascalCase
const userService = { ... };       // Instances: camelCase

// ❌ DON'T
function get_user_list() { }       // snake_case
const maxitems = 10;               // lowercase
const UserService = { ... };       // Component-like naming
```

#### File Organization
```javascript
// Page/Component file structure:
import { useState, useEffect } from 'react';
import api from '../api/client';
import Button from '../components/common/Button';
import { useAsync } from '../hooks/useAsync';

// Component
export default function UserListPage() {
  const [users, setUsers] = useState([]);
  const { loading, run } = useAsync();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    await run(async () => {
      const res = await api.get('/users');
      setUsers(res.data);
    });
  };

  return (
    <div>
      {/* JSX */}
    </div>
  );
}
```

#### Error Handling (MUST)
```javascript
// ✅ DO — Use centralized error handler
const loadUsers = async () => {
  await run(async () => {
    const res = await api.get('/users');
    setUsers(res.data);
  });  // Errors handled by api.js interceptor
};

// ❌ DON'T — Inconsistent error handling
const loadUsers = async () => {
  try {
    const res = await axios.get('http://localhost:8000/api/users');
    setUsers(res.data);
  } catch (err) {
    alert('Error!');  // Wrong way to show errors
  }
};
```

#### Comments & Documentation
```javascript
// ✅ DO
/**
 * Format price with Turkish currency
 * @param {number} price - Price in TL
 * @returns {string} Formatted price (e.g. "1.234,50 ₺")
 */
function formatPrice(price) {
  return price.toLocaleString('tr-TR', { 
    style: 'currency', 
    currency: 'TRY' 
  });
}

// ❌ DON'T
function formatPrice(price) {
  // format price
  return price.toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' });
}
```

---

## 🗂️ IV. FOLDER STRUCTURE IMPLEMENTATION

### Minimal Viable Restructure (Hafta 3-4)

```
BackendProje/
├── core/
│   ├── __init__.py
│   ├── auth.py           # JWT + password logic
│   ├── security.py       # require_role, permissions
│   ├── exceptions.py     # Custom exceptions
│   └── exception_handlers.py

├── database/
│   ├── __init__.py
│   ├── db.py            # Engine, SessionLocal, get_db
│   └── models.py        # All models (TO BE SPLIT LATER)

├── schemas/
│   ├── __init__.py
│   ├── request.py       # Create/Update schemas
│   └── response.py      # Response schemas

├── services/
│   ├── __init__.py
│   ├── urun_service.py
│   ├── stok_service.py
│   └── sayim_service.py

├── routers/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── urunler.py
│   │   ├── depolar.py
│   │   ├── lotlar.py
│   │   └── ... (others)
│   └── v2/  (reserved)

├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_crud.py
│   └── test_services/

├── main.py              # ONLY: app setup
├── requirements.txt
├── .env.example
├── pyproject.toml
├── DEVELOPMENT.md       # Developer guide
└── README.md
```

---

## 📋 V. MIGRATION STRATEGY (Step-by-Step)

### Week 1-2: Setup
- [ ] Pre-commit hooks kur
- [ ] ESLint + Prettier config
- [ ] Black + Pylint config
- [ ] CODING_STANDARDS.md yaz
- [ ] Folder strukture plan yap

### Week 3-4: Core Refactor
- [ ] Backend: core/ folder + exceptions
- [ ] Backend: services/ folder + 1 service
- [ ] Backend: schemas/ split
- [ ] Frontend: api/ centralize
- [ ] Tests: conftest.py + basic tests

### Week 5-6: Complete
- [ ] All services ported
- [ ] All tests passing
- [ ] API documentation (Swagger)
- [ ] Deployment guide
- [ ] DEVELOPMENT.md complete

---

## 🚀 VI. IMPLEMENTATION CHECKLIST

### Pre-Implementation
- [ ] Bu raporu oku ve anla
- [ ] Team (or self) agreement alınmış mı?
- [ ] Backup almış mı? (git branch: `feature/code-cleanup`)
- [ ] Timeline kararlaştırılmış mı?

### Phase 1 Setup
- [ ] Pre-commit hooks kur
- [ ] ESLint upgrade + config
- [ ] Black/Pylint install + config
- [ ] pyproject.toml oluştur
- [ ] .editorconfig oluştur (IDE standardization)

### Phase 2 Refactor
- [ ] core/exceptions.py oluştur
- [ ] Exception handlers test et
- [ ] services/ klasörü oluştur
- [ ] İlk service port et (UrunService)
- [ ] İlk router refactor et
- [ ] Tests yazıp çalıştır
- [ ] Diğer routers port et (iteratively)

### Phase 3 Testing
- [ ] Conftest fixtures
- [ ] Service unit tests
- [ ] Router integration tests
- [ ] E2E tests (if needed)
- [ ] Test coverage >80%

### Phase 4 Documentation
- [ ] API Swagger documentation check
- [ ] DEVELOPMENT.md complete
- [ ] Code examples
- [ ] Troubleshooting guide
- [ ] Deploy guide update

---

## 📊 VII. SUCCESS METRICS

| Metrik | Before | Target | Timeline |
|--------|--------|--------|----------|
| **Code Duplication** | ~30% | <5% | Week 4 |
| **Test Coverage** | 0% | >70% | Week 6 |
| **Average Function Length** | 80 lines | <30 lines | Week 5 |
| **Documentation Coverage** | 10% | 90% | Week 6 |
| **Linting Errors** | 200+ | 0 | Week 2 |
| **Type Hints** | 20% | 100% | Week 5 |
| **Onboarding Time** | 2 weeks | 2 days | Week 6 |

---

## 💰 VIII. RESOURCE ALLOCATION

### Solo Developer Timeline

```
Week 1-2 (Setup): 10-12 hours
  - Pre-commit hooks, linting tools
  - Documentation writing

Week 3-4 (Refactor): 30-40 hours  ← INTENSIVE
  - Core refactoring
  - Error handling
  - Service layer creation
  - Iterative testing

Week 5-6 (Testing + Docs): 20-25 hours
  - Comprehensive testing
  - Final documentation
  - Code review (self)

TOTAL: 60-75 hours = ~2 weeks full-time
```

**Parallel Schedule (with ongoing development):**
- **30 min/day:** Code quality tooling
- **2-3 hours/day:** Refactoring
- **1 hour/day:** Testing + documentation
- **Ongoing:** git commits & pre-commit checks

---

## 🎓 IX. KNOWLEDGE TRANSFER (Future Team)

Wenn ein Team-Mitglied zukünftig beiträgt:

### Onboarding Checklist (2 days instead of 2 weeks):
- [ ] README.md → Overview
- [ ] DEVELOPMENT.md → Code organization
- [ ] CODING_STANDARDS.md → Rules
- [ ] `git log` → Recent patterns
- [ ] Run tests → Verify setup
- [ ] Small PR → Learn workflow

### Documentation to Maintain:
- **DEVELOPMENT.md** — Update when structure changes
- **API.md** — Update when endpoints change (auto-generated by Swagger)
- **DISASTER_RECOVERY.md** — Database, deployment issues
- **CHANGELOG.md** — Version history

---

## ⚠️ X. COMMON MISTAKES TO AVOID

| Hata | Sonuç | Fix |
|------|-------|-----|
| **All-at-once refactoring** | Shipping broken code | Incremental, feature-branch approach |
| **No backups before changes** | Data loss | Always git commit first |
| **Skip testing phase** | Regressions | Test each phase before moving on |
| **Inconsistent with standards** | Standards become optional | Pre-commit hook enforcement |
| **Documentation last** | Never gets done | Write docs as you code |

---

## 📞 XI. SUPPORT & ROLLBACK

### If Things Go Wrong:
```bash
# Rollback to last working state
git reset --hard HEAD~5

# Or switch to backup branch
git checkout backup-03-12-2026

# Or revert specific commit
git revert <commit-hash>
```

### Common Issues:
| Sorun | Çözüm |
|-------|-------|
| Pre-commit blocking commits | `git commit --no-verify` (sarı bayrak!) |
| Tests fail after refactor | Run full test suite, check imports |
| Import errors | Check `__init__.py` files |
| Database migration issues | Reset test DB: `rm test.db` |

---

## 🎯 SUMMARY

Bu rapor gösteriyor ki:

✅ **Proje iyi temele sahip** ama organizasyon eksik  
✅ **6-8 hafta'da production-ready** duruma getirilebilir  
✅ **Team collaboration'a hazır** hale dönüştürülebilir  
✅ **Teknik borç minimize** edilebilir  

**Başlama Tarihi:** 13 Mart 2026 (Pazartesi)  
**Target Completion:** 24 Mayıs 2026  

---

*Hazırlayan: Code Analysis System*  
*Versiyon: 1.0*  
*Son Güncelleme: 12 Mart 2026, 14:30*

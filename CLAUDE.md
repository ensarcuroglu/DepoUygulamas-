# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Depo Yönetim Sistemi** — A warehouse management system (WMS) with lot/pallet tracking. Full-stack application: FastAPI backend + React (Vite) frontend.

---

## Running the Project

### Backend (FastAPI)
```bash
cd BackendProje

# Install dependencies
pip install -r requirements.txt

# Configure environment — create a .env file with:
# DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME (MySQL)
# JWT_SECRET_KEY

# Start the development server
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Seed initial data (admin + depocu users)
python seed.py
```

API docs available at: `http://localhost:8000/docs`

### Frontend (React + Vite)
```bash
cd ReactProje

# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev

# Lint
npm run lint

# Production build
npm run build
```

---

## Architecture

### Backend (`BackendProje/`)

- **`main.py`** — FastAPI app entry point; registers all routers, CORS config, and the `/api/dashboard` endpoint
- **`database.py`** — SQLAlchemy engine setup reading MySQL connection from `.env` (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`)
- **`models.py`** — All SQLAlchemy ORM models: `Marka`, `Kategori`, `Depo`, `Raf`, `Tedarikci`, `Urun`, `Lot`, `Palet`, `StokHareketi`, `SistemLog`, `Kullanici`, `DestekTalebi`
- **`schemas.py`** — Pydantic request/response models
- **`crud.py`** — Business logic layer (DB queries)
- **`auth.py`** — JWT token creation/validation (`python-jose`), bcrypt password hashing (`passlib`), `get_current_user` dependency, `require_role()` factory
- **`routers/`** — One router file per entity: `auth`, `urunler`, `kategoriler`, `depolar`, `raflar`, `lotlar`, `paletler`, `stok_hareketleri`, `kullanicilar`, `tedarikciler`, `markalar`, `sistem_loglari`, `destek`

**Key data flow:** `Urun` stock level (`stok_miktari`) is computed as a SQLAlchemy `column_property` — it aggregates `Palet.koli_adedi` through active `Lot` records (no stored stock count column on `Urun`).

**Roles:** `admin`, `depocu`, `goruntuleyen`, `lojistik`

**JWT config:** `JWT_SECRET_KEY` env var (falls back to hardcoded default — must be overridden in production). Token expires in 8 hours.

### Frontend (`ReactProje/src/`)

- **`App.jsx`** — Route definitions with nested `PrivateRoute` (auth check) and `RoleRoute` (role check). Default redirect: `depocu`/`lojistik` → `/stok-hareketleri`; `admin` → `/dashboard`
- **`contexts/AuthContext.jsx`** — Auth state: token + user stored in `localStorage`; validates on load via `GET /api/auth/me`
- **`services/api.js`** — Axios instance with base URL `http://localhost:8000/api`; request interceptor adds Bearer token; response interceptor auto-redirects to `/login` on 401
- **`components/layout/`** — `DashboardLayout`, `Header`, `Sidebar`
- **`components/PrivateRoute.jsx`** / **`RoleRoute.jsx`** — Route guards
- **`pages/`** — One page component per feature area
- **`utils/exportUtils.js`** — Excel (xlsx) and PDF (jspdf + jspdf-autotable) export helpers
- **`utils/hata.js`** — API error message resolver (`hataMetni(err, fallback)`); checks FastAPI `detail`, `message`, JS message in order
- **`hooks/useAsync.js`** — `useAsync(initialLoading?)` hook; centralizes `loading` state via `run(asyncFn)` — used across all data-fetching pages

**Route access control:**
- Admin only: `/dashboard`, `/urunler`, `/kategoriler`, `/lotlar`, `/paletler`, `/kullanicilar`, `/ayarlar`, `/tedarikciler`, `/sistem-loglari`
- Admin + Lojistik: `/depolar`, `/depo-kroki`
- All authenticated: `/stok-hareketleri`, `/sevkiyatlar`, `/profil-ayarlari`, `/destek-masasi`

---

## Environment Variables

Create `BackendProje/.env`:
```
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=3306
DB_NAME=depo_db
JWT_SECRET_KEY=<strong-random-secret>
```

---

## Key Conventions

- All naming is in Turkish (models, variables, API endpoints, UI labels)
- API endpoints follow pattern `/api/<resource>/` (plural Turkish names)
- Backend routers use `Depends(get_current_user)` or `Depends(require_role("admin"))` for auth
- `SistemLog` records are written manually from routers when critical operations occur (CREATE/UPDATE/DELETE)
- `Palet.aktif=False` marks a pallet as shipped/removed; `Lot.aktif=False` marks a lot as closed

## Code Review Standards

After completing any implementation, review the code for:
- Functions longer than 30 lines (likely doing too much)
- Logic duplicated more than twice (extract to utility)
- Any `any` type usage in JavaScript (replace with real types)
- Components with more than 3 props that could be grouped into an object
- Missing error handling on async operations


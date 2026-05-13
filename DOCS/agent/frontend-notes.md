# Frontend Notes (ReactProje/)

React 19 + Vite 7. TypeScript yok; `.js` / `.jsx`. Mimari detay için `project-architecture.md`.

## Komutlar

```bash
cd ReactProje

npm install
npm run dev        # manual local, HTTPS/HTTP env'e bagli
npm run lint       # ESLint 9 flat config
npm run build      # production
npm run preview    # production build serve
```

## Kurallar

- TypeScript ekleme yasak — tüm yeni dosyalar `.js` / `.jsx`.
- Fonksiyonel component + hooks.
- Data fetching TanStack React Query; query key pattern'ine uy (`queryKeys.js`).
- Query hook dosyaları domain-based: `<domain>Queries.js`.
- Service dosyaları: `<domain>Api.js`.
- HTTP: Axios `services/api.js`; auto Bearer; 401 → refresh → fallback logout.
- State: Context (Auth, Theme) + React Query cache.
- Styling: Tailwind CSS v4 vite plugin; custom CSS `index.css` içinde.
- Error: `hataMetni(err, fallback)`; sıralama `detail` → `message` → JS `message`.
- Toast: `react-hot-toast`. Export: `exportUtils.js`.
- Route guards: `PrivateRoute` (auth) + `RoleRoute` (rol).

## Layoutlar

- `DashboardLayout` — admin/lojistik ve ortak korumalı sayfalar.
- `DepocuLayout` — sadece depocu.
- `TerminalLayout` — mobil terminal.

## PWA

- vite-plugin-pwa + workbox.
- Standalone mode, portrait.
- `public/` altında manifest + ikonlar.

## Vite Yapılandırması

- Compose dev: HTTP (`VITE_DEV_HTTPS=false`).
- Manuel local: `VITE_DEV_HTTPS=true` → mkcert/HTTPS.
- `/api` proxy hedefi `VITE_BACKEND_PROXY_TARGET` (Compose: `http://backend:8000`, local: `http://127.0.0.1:8000`).
- `server.host: true` — LAN erişimi.
- Build chunk'ları elle bölünmüş: `react-vendor`, `chart-vendor`, `excel-vendor`, `pdf-vendor`, `barcode-vendor`, `ui-vendor`.
- `/ws/agv` ws:true proxy `/api` proxy'sinden ÖNCE tanımlanır.

## AGV İzleme UI

- Three.js + @react-three/fiber + @react-three/drei + zustand.
- Yüksek frekans veri React state'e yazılmaz; `useAgvStore.getState()` ile `useFrame` içinde oku ve lerp et. Aksi halde 5-10 Hz re-render tüm sayfayı yavaşlatır.
- Route: `/agv-izleme` (`VITE_FEATURE_AGV_ENABLED=true` ile açılır).

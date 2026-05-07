import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import mkcert from 'vite-plugin-mkcert'
import { visualizer } from "rollup-plugin-visualizer"
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    mkcert(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: false,
      includeAssets: [
        'icons/depo-icon.svg',
        'icons/apple-touch-icon-180.png',
        'fonts/**/*',
      ],
      manifest: {
        name: 'Depo Yönetim Sistemi',
        short_name: 'DepoTerminal',
        description: 'Saha operatörü için scan-to-verify yerleştirme ve depo yönetim terminali',
        lang: 'tr',
        dir: 'ltr',
        start_url: '/terminal/gorevler',
        scope: '/',
        display: 'standalone',
        display_override: ['standalone', 'minimal-ui'],
        orientation: 'portrait-primary',
        background_color: '#0f172a',
        theme_color: '#0f172a',
        categories: ['business', 'productivity', 'utilities'],
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/icons/icon-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
        shortcuts: [
          {
            name: 'Görev Listesi',
            short_name: 'Görevler',
            description: 'Aktif yerleştirme/toplama görevleri',
            url: '/terminal/gorevler',
            icons: [{ src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' }],
          },
          {
            name: 'Üretim Paleti Kabul',
            short_name: 'Üretim Kabul',
            description: 'Üretimden gelen palet kabul ekranı',
            url: '/terminal/uretim-kabul',
            icons: [{ src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' }],
          },
          {
            name: 'Stok İşlemleri',
            short_name: 'Stok',
            description: 'Stok giriş ve çıkış işlemleri',
            url: '/stok-hareketleri',
            icons: [{ src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' }],
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff,woff2}'],
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//],
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: false,
        runtimeCaching: [
          {
            urlPattern: ({ url, request }) =>
              url.pathname.startsWith('/api/') && request.method === 'GET',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'depo-api-get',
              networkTimeoutSeconds: 3,
              expiration: { maxEntries: 50, maxAgeSeconds: 60 * 5 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: ({ request }) =>
              ['style', 'script', 'worker'].includes(request.destination),
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'depo-static-assets' },
          },
          {
            urlPattern: ({ request }) =>
              ['image', 'font'].includes(request.destination),
            handler: 'CacheFirst',
            options: {
              cacheName: 'depo-media',
              expiration: { maxEntries: 60, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      devOptions: {
        enabled: true,
        type: 'module',
        navigateFallback: '/index.html',
      },
    }),
    visualizer({
      open: true,          // Build bittiğinde raporu tarayıcıda otomatik açar
      filename: "stats.html", // Analiz dosyasının adı
      gzipSize: true,        // Sıkıştırılmış boyutları gösterir
      brotliSize: true,      // Daha gelişmiş sıkıştırma boyutlarını gösterir
    }),
  ],
  server: {
    https: true,
    host: true, // Vite'in 0.0.0.0 üzerinden yerel ağa açılmasını sağlar
    allowedHosts: true, // BÜTÜN TÜNEL LİNKLERİNE İZİN VEREN SATIR
    
    // =======================================================
    // EKLENEN KISIM: ZAP Güvenlik Başlıkları (Security Headers)
    // =======================================================
    headers: {
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' https: http: wss: ws:;",
      'X-Frame-Options': 'DENY',
      'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
      'X-Content-Type-Options': 'nosniff'
    },

    proxy: {
      // AGV servisi (port 8002) — /api öncesinde eşleşmesi için ÖNCE tanımlı
      '/api/agv': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
      },
      '/ws/agv': {
        target: 'ws://127.0.0.1:8002',
        ws: true,
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            if (err.code === 'ECONNRESET') {
              // React Hot-Reload veya sayfa yenilemede sıkça oluşan zararsız hatayı gizle
              return;
            }
            console.error('Vite WS Proxy Error:', err.message);
          });
        }
      },
      // React'tan gelen istekleri Python (FastAPI/Uvicorn) backend'ine yönlendirir
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  // EKLENEN KISIM: Ağır kütüphaneleri ana paketten (bundle) ayırma ayarları
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Temel React kütüphaneleri (her sayfada lazım olanlar)
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          
          // Sadece grafik olan sayfalarda yüklenecek
          'chart-vendor': ['recharts'],
          
          // Sadece Excel/Raporlama işlemlerinde yüklenecek
          'excel-vendor': ['xlsx'],
          
          // Sadece PDF çıktısı alınan yerlerde yüklenecek
          'pdf-vendor': ['jspdf', 'jspdf-autotable'],
          
          // Sadece Terminal ve Barkod okuma sayfalarında yüklenecek
          'barcode-vendor': ['@zxing/library', 'html5-qrcode', 'qrcode.react'],

          // İkonlar ve bildirimler
          'ui-vendor': ['lucide-react', 'react-hot-toast'],

          // Sadece /agv-izleme sayfasında yüklenecek (Three.js + R3F + zustand)
          'agv-vendor': ['three', '@react-three/fiber', '@react-three/drei', 'zustand']
        }
      }
    },
    // Uyarı sınırını biraz yükseltebiliriz, çünkü parçalara ayırdık
    chunkSizeWarningLimit: 800,
  }
})
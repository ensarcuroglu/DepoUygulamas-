import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import mkcert from 'vite-plugin-mkcert'
import { visualizer } from "rollup-plugin-visualizer"

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    mkcert(),
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
    proxy: {
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
          'ui-vendor': ['lucide-react', 'react-hot-toast']
        }
      }
    },
    // Uyarı sınırını biraz yükseltebiliriz, çünkü parçalara ayırdık
    chunkSizeWarningLimit: 800,
  }
})
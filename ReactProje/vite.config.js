import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import mkcert from 'vite-plugin-mkcert'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    mkcert(),
  ],
  server: {
    https: true,
    host: true, // Vite'in 0.0.0.0 üzerinden yerel ağa açılmasını sağlar
    allowedHosts: true, // <-- BÜTÜN TÜNEL LİNKLERİNE İZİN VEREN SATIR
    proxy: {
      // React'tan gelen istekleri Python (Uvicorn) backend'ine yönlendirir
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
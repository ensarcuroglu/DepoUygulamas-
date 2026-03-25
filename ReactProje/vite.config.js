import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    host: true, // Vite'in 0.0.0.0 üzerinden yerel ağa açılmasını sağlar
    proxy: {
      // React'tan gelen istekleri Python (Uvicorn) backend'ine yönlendirir
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
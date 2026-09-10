import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite configuration with proxy to backend and 0.0.0.0 host binding
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})

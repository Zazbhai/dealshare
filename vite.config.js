import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // Allow external connections
    allowedHosts: [
      'dealshare.heyalex.store',
      'api.dealshare.heyalex.store',
      'localhost',
      '.heyalex.store' // Allows all subdomains
    ],
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
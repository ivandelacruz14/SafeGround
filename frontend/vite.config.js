import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Same-origin in development so the httpOnly refresh cookie works without CORS.
    proxy: { '/api': { target: process.env.VITE_PROXY_TARGET || 'http://localhost:5000', changeOrigin: false } },
  },
  test: { environment: 'jsdom', setupFiles: './src/test/setup.js', globals: true, css: false },
})

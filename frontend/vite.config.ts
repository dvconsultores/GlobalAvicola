import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// API proxy target — overridable so the same config works locally
// (http://localhost:8000) and inside Docker (http://backend:8000).
const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    // Listen on all interfaces so the dev server is reachable from outside
    // the container; `true` === 0.0.0.0.
    host: true,
    // In Docker bind mounts on some hosts, inotify events are not delivered;
    // enable polling via VITE_USE_POLLING=true for reliable HMR.
    watch: {
      usePolling: process.env.VITE_USE_POLLING === 'true',
    },
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 2000,
    sourcemap: false,
  },
})

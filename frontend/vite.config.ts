import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// API proxy target — overridable so the same config works locally
// (http://localhost:8000) and inside Docker (http://backend:8000).
const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

// SPEC 016 §B (D-B3): procedencia exacta del build.
// La imagen no contiene `.git`, así que el SHA y la fecha llegan por entorno desde el
// `Dockerfile` (build-args) o desde el shell. Sin ellos, `unknown`: nunca se le pregunta
// al repositorio qué se construyó.
const gitSha = process.env.GIT_SHA || 'unknown'
const buildTime = process.env.BUILD_TIME || 'unknown'

/**
 * SPEC 016 §B: emite `dist/version.json` con la procedencia del build.
 * Solo actúa en build (`apply: 'build'`); no interviene en el dev server ni en vitest.
 */
function gaBuildProvenance(): Plugin {
  return {
    name: 'ga-build-provenance',
    apply: 'build',
    generateBundle() {
      this.emitFile({
        type: 'asset',
        fileName: 'version.json',
        source: JSON.stringify({ git_sha: gitSha, build_time: buildTime }),
      })
    },
  }
}

export default defineConfig({
  plugins: [gaBuildProvenance(), react(), tailwindcss()],
  define: {
    __GA_BUILD_SHA__: JSON.stringify(gitSha),
    __GA_BUILD_TIME__: JSON.stringify(buildTime),
  },
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

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // SPEC 016 §B (D-B3): los globals del build los inyecta `define`; en tests valen
  // 'test' para que el código que los lee compile y se ejecute sin tocar `process.env`.
  define: {
    __GA_BUILD_SHA__: JSON.stringify('test'),
    __GA_BUILD_TIME__: JSON.stringify('test'),
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    css: false,
  },
})

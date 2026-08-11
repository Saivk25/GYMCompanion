/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@assets': path.resolve(__dirname, './src/assets'),
      '@engine': path.resolve(__dirname, './src/engine'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@layouts': path.resolve(__dirname, './src/layouts'),
      '@systems': path.resolve(__dirname, './src/systems'),
      '@vision': path.resolve(__dirname, './src/vision'),
      '@rendering': path.resolve(__dirname, './src/rendering'),
      '@experience': path.resolve(__dirname, './src/experience'),
      '@particles': path.resolve(__dirname, './src/particles'),
      '@physics': path.resolve(__dirname, './src/physics'),
      '@gestures': path.resolve(__dirname, './src/gestures'),
      '@themes': path.resolve(__dirname, './src/themes'),
      '@animations': path.resolve(__dirname, './src/animations'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@app-types': path.resolve(__dirname, './src/types'),
      '@constants': path.resolve(__dirname, './src/constants'),
      '@services': path.resolve(__dirname, './src/services'),
    },
  },
  server: {
    host: true,
    port: 5173,
  },
  build: {
    target: 'esnext',
    sourcemap: true,
    chunkSizeWarningLimit: 1000,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    css: false,
  },
})

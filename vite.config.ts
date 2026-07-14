import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths";

const apiOrigin = process.env.SMR_API_ORIGIN || 'http://127.0.0.1:3000'

// https://vite.dev/config/
export default defineConfig({
  build: {
    sourcemap: 'hidden',
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: apiOrigin,
        changeOrigin: true,
      },
    },
  },
  plugins: [
    react(),
    tsconfigPaths()
  ],
})

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: { proxy: {
    '/api': process.env.ASTRA_API_PROXY_TARGET || 'http://127.0.0.1:8000',
    '/agent': process.env.ASTRA_AGENT_PROXY_TARGET || 'http://127.0.0.1:8010',
  } },
})

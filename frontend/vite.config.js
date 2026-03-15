import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/users': 'http://localhost:8000',
      '/pose': 'http://localhost:8000',
      '/workout': 'http://localhost:8000',
      '/analytics': 'http://localhost:8000',
    }
  }
})

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// Backend started with uvicorn on this address; /api is forwarded to it in real mode.
const API_TARGET = 'http://127.0.0.1:8000';
const apiProxy = {
  '/api': { target: API_TARGET, changeOrigin: true },
};

export default defineConfig({
  plugins: [react()],
  server: { proxy: apiProxy },
  preview: { proxy: apiProxy },
});

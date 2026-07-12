import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  root: path.resolve(__dirname),
  build: {
    outDir: path.resolve(__dirname, '..', 'static'),
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    historyApiFallback: true,
  },
})

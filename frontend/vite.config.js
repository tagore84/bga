// frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'


export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // Alias al fichero .mjs que expone el módulo ESM
      'vue-konva$': path.resolve(
        __dirname,
        'node_modules/vue-konva/dist/vue-konva.mjs'
      ),
      '@': path.resolve(__dirname, './src')
    }
  }
})
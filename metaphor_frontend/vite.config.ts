import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import svgr from "vite-plugin-svgr";




// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), svgr()],
  server:{
    proxy: {
      // 本地后端
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      // 如果后端在服务器且做了 ssh 转发，仍然是 localhost:8000
    }
  }
})


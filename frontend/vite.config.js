import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import history from 'connect-history-api-fallback'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    // 👇 dev 서버에 직접 history fallback 미들웨어 붙이기
    middlewareMode: false,
    configureServer: (server) => {
      server.middlewares.use(
        history({
          index: '/index.html',
        })
      )
    },
  },
})

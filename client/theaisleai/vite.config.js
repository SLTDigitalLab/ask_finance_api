// import { defineConfig } from 'vite'
// import react from '@vitejs/plugin-react'

// // https://vitejs.dev/config/
// export default defineConfig({
//   plugins: [react()],
//   exclude: ['recharts'],
// })


import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  exclude: ["recharts"],
  server: {
    proxy: {
      "/copilot": {
        target: "http://localhost:5003",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/copilot/, ""),
      },
    },
  },
});

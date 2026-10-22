// vite.config.js
import { defineConfig } from "file:///sessions/ecstatic-exciting-tesla/mnt/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D1%8B%D0%B8%CC%86_%D0%BC%D0%B0%D0%B3%D0%B0%D0%B7%D0%B8%D0%BD/frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///sessions/ecstatic-exciting-tesla/mnt/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D1%8B%D0%B8%CC%86_%D0%BC%D0%B0%D0%B3%D0%B0%D0%B7%D0%B8%D0%BD/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { resolve } from "path";
var __vite_injected_original_dirname = "/sessions/ecstatic-exciting-tesla/mnt/\u0421\u0442\u0440\u043E\u0438\u0442\u0435\u043B\u044C\u043D\u044B\u0438\u0306_\u043C\u0430\u0433\u0430\u0437\u0438\u043D/frontend";
var vite_config_default = defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { "@": resolve(__vite_injected_original_dirname, "src") }
  },
  server: {
    port: 3e3,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: "../app/static/dist",
    emptyOutDir: true,
    sourcemap: false
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvc2Vzc2lvbnMvZWNzdGF0aWMtZXhjaXRpbmctdGVzbGEvbW50L1x1MDQyMVx1MDQ0Mlx1MDQ0MFx1MDQzRVx1MDQzOFx1MDQ0Mlx1MDQzNVx1MDQzQlx1MDQ0Q1x1MDQzRFx1MDQ0Qlx1MDQzOFx1MDMwNl9cdTA0M0NcdTA0MzBcdTA0MzNcdTA0MzBcdTA0MzdcdTA0MzhcdTA0M0QvZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIi9zZXNzaW9ucy9lY3N0YXRpYy1leGNpdGluZy10ZXNsYS9tbnQvXHUwNDIxXHUwNDQyXHUwNDQwXHUwNDNFXHUwNDM4XHUwNDQyXHUwNDM1XHUwNDNCXHUwNDRDXHUwNDNEXHUwNDRCXHUwNDM4XHUwMzA2X1x1MDQzQ1x1MDQzMFx1MDQzM1x1MDQzMFx1MDQzN1x1MDQzOFx1MDQzRC9mcm9udGVuZC92aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vc2Vzc2lvbnMvZWNzdGF0aWMtZXhjaXRpbmctdGVzbGEvbW50LyVEMCVBMSVEMSU4MiVEMSU4MCVEMCVCRSVEMCVCOCVEMSU4MiVEMCVCNSVEMCVCQiVEMSU4QyVEMCVCRCVEMSU4QiVEMCVCOCVDQyU4Nl8lRDAlQkMlRDAlQjAlRDAlQjMlRDAlQjAlRDAlQjclRDAlQjglRDAlQkQvZnJvbnRlbmQvdml0ZS5jb25maWcuanNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXG5pbXBvcnQgeyByZXNvbHZlIH0gZnJvbSAncGF0aCdcblxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcbiAgcGx1Z2luczogW3Z1ZSgpXSxcbiAgcmVzb2x2ZToge1xuICAgIGFsaWFzOiB7ICdAJzogcmVzb2x2ZShfX2Rpcm5hbWUsICdzcmMnKSB9XG4gIH0sXG4gIHNlcnZlcjoge1xuICAgIHBvcnQ6IDMwMDAsXG4gICAgcHJveHk6IHtcbiAgICAgICcvYXBpJzoge1xuICAgICAgICB0YXJnZXQ6ICdodHRwOi8vbG9jYWxob3N0OjgwMDAnLFxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWVcbiAgICAgIH1cbiAgICB9XG4gIH0sXG4gIGJ1aWxkOiB7XG4gICAgb3V0RGlyOiAnLi4vYXBwL3N0YXRpYy9kaXN0JyxcbiAgICBlbXB0eU91dERpcjogdHJ1ZSxcbiAgICBzb3VyY2VtYXA6IGZhbHNlXG4gIH1cbn0pXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQWtlLFNBQVMsb0JBQW9CO0FBQy9mLE9BQU8sU0FBUztBQUNoQixTQUFTLGVBQWU7QUFGeEIsSUFBTSxtQ0FBbUM7QUFJekMsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDMUIsU0FBUyxDQUFDLElBQUksQ0FBQztBQUFBLEVBQ2YsU0FBUztBQUFBLElBQ1AsT0FBTyxFQUFFLEtBQUssUUFBUSxrQ0FBVyxLQUFLLEVBQUU7QUFBQSxFQUMxQztBQUFBLEVBQ0EsUUFBUTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sT0FBTztBQUFBLE1BQ0wsUUFBUTtBQUFBLFFBQ04sUUFBUTtBQUFBLFFBQ1IsY0FBYztBQUFBLE1BQ2hCO0FBQUEsSUFDRjtBQUFBLEVBQ0Y7QUFBQSxFQUNBLE9BQU87QUFBQSxJQUNMLFFBQVE7QUFBQSxJQUNSLGFBQWE7QUFBQSxJQUNiLFdBQVc7QUFBQSxFQUNiO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K

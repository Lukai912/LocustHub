import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
  },
  build: {
    // Node 18.8 in the local Codex environment hangs in the minifier path.
    // Keep Stage 4 builds deterministic; production compression can be handled
    // by Nginx/CDN or revisited when the runtime Node version is upgraded.
    minify: false,
  },
});

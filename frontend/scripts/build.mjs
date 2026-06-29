import vue from '@vitejs/plugin-vue';
import { build } from 'vite';

await build({
  configFile: false,
  root: process.cwd(),
  plugins: [vue()],
  clearScreen: false,
  build: {
    minify: false,
  },
});

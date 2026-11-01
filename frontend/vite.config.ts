import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// Same origin in every environment (AD-7, Story 1.7): the frontend calls relative /api paths,
// and the dev and preview servers forward them to FastAPI. 127.0.0.1 rather than localhost,
// because Node may resolve localhost to ::1 while uvicorn listens on IPv4 only.
export const apiProxy = { '/api': 'http://127.0.0.1:8000' };

// The service worker is its own build input, emitted as /service-worker.js at the site root
// so its scope can be "/" (AD-12). It is only registered in production builds.
// It is registered as a classic script: src/service-worker.ts must stay import-free until
// registration uses { type: 'module' } (Trinn 2 push).
export default defineConfig({
  plugins: [react()],
  server: { proxy: apiProxy },
  preview: { proxy: apiProxy },
  build: {
    rolldownOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        'service-worker': fileURLToPath(new URL('./src/service-worker.ts', import.meta.url)),
      },
      output: {
        entryFileNames: (chunk) =>
          chunk.name === 'service-worker' ? 'service-worker.js' : 'assets/[name]-[hash].js',
      },
    },
  },
  test: {
    globals: true,
    // Two projects, because src/test-setup.ts needs jsdom while the config test runs in Node.
    projects: [
      {
        extends: true,
        test: {
          name: 'app',
          include: ['src/**/*.test.{ts,tsx}'],
          environment: 'jsdom',
          setupFiles: ['./src/test-setup.ts'],
        },
      },
      {
        extends: true,
        test: { name: 'config', include: ['vite.config.test.ts'], environment: 'node' },
      },
    ],
  },
});

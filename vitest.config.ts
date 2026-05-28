import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    tags: [
      { name: 'example', timeout: 30_000}
    ],
  },
});

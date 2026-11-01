// @vitest-environment node
// Story 1.7 (AD-7): /api goes to the backend through the Vite proxy, in dev and in preview.
import { describe, expect, it } from 'vitest';
import config, { apiProxy } from './vite.config';

describe('vite config', () => {
  it('proxies /api to the backend on 127.0.0.1:8000', () => {
    expect(apiProxy).toEqual({ '/api': 'http://127.0.0.1:8000' });
  });

  it('uses the same proxy for the dev and the preview server', () => {
    expect(config.server?.proxy).toBe(apiProxy);
    expect(config.preview?.proxy).toBe(apiProxy);
  });
});

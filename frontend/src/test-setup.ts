import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';

// jsdom has no matchMedia; default to "no media query matches".
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Browsers resolve a relative URL in `new Request('/api/...')` against the page; Node's Request
// (used under jsdom) does not. Resolve it the browser way, so the API client keeps relative paths.
const NodeRequest = globalThis.Request;
globalThis.Request = class extends NodeRequest {
  constructor(input: RequestInfo | URL, init?: RequestInit) {
    super(typeof input === 'string' ? new URL(input, window.location.href) : input, init);
  }
};

afterEach(() => {
  cleanup();
  // Story 2.2: the most recently used Home is kept in localStorage; no test inherits another's.
  localStorage.clear();
});

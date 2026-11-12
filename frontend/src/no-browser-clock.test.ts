// Epic 2 retro, action 4 (R1): the frontend never reads the browser's clock. «Today», the due
// status and the day words come from the server (Story 2.2), so a browser in another time zone or
// with a wrong clock shows the same text. The only exception is the install prompt, which stores
// a timestamp and shows nothing from it.
const sources = import.meta.glob(['./**/*.ts', './**/*.tsx', '!./**/*.test.*', '!./test-utils/**'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const ALLOWED = ['./components/InstallPrompt.tsx'];

describe('the browser clock', () => {
  it('is read nowhere in the app code, except the install prompt flag', () => {
    expect(Object.keys(sources).length).toBeGreaterThan(20);
    const readers = Object.entries(sources)
      .filter(([path, code]) => !ALLOWED.includes(path) && /new Date\(\)|Date\.now\(\)/.test(code))
      .map(([path]) => path);
    expect(readers).toEqual([]);
  });
});

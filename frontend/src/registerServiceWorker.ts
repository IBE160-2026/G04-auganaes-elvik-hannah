/**
 * Registers /service-worker.js with scope "/" (AD-12). Production builds only:
 * the dev server serves the worker as an ES module from /src, which would break scope.
 */
export function registerServiceWorker(): void {
  if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return;

  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).catch((error: unknown) => {
      console.error('Kunne ikke registrere service worker', error);
    });
  });
}

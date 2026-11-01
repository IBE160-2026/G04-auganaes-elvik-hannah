/// <reference lib="webworker" />
// Installable PWA shell (Story 1.1, AD-12). It only installs and takes control: no caching,
// so it can never serve stale code. Web Push handlers are added in Trinn 2 (AD-8).
declare const self: ServiceWorkerGlobalScope;

self.addEventListener('install', () => {
  void self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

export {};

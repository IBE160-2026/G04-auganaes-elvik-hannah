/// <reference lib="webworker" />
// Installable PWA shell (Story 1.1, AD-12). It installs and takes control but caches nothing, so
// it can never serve stale code. Story 3.1 adds the two Web Push handlers (AD-8): show what the
// server sent, and open its link on a tap. The text and the links are Story 3.2's. It is a
// classic script, so it must stay import-free.
declare const self: ServiceWorkerGlobalScope;

type PushPayload = { title?: unknown; body?: unknown; url?: unknown };

/**
 * Only an address on this origin is opened, as a path; anything else falls back to the root. It
 * is resolved the way the browser does, so «//host» and «/\\host» (a backslash counts as a slash)
 * are caught as well as «https://host».
 */
function appPath(url: unknown): string {
  if (typeof url !== 'string') return '/';
  try {
    const target = new URL(url, self.location.origin);
    return target.origin === self.location.origin ? target.pathname + target.search + target.hash : '/';
  } catch {
    return '/';
  }
}

self.addEventListener('install', () => {
  void self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  let payload: PushPayload = {};
  try {
    payload = (event.data?.json() ?? {}) as PushPayload;
  } catch {
    // Not JSON: still show something, since a subscription made with userVisibleOnly must.
  }
  const title = typeof payload.title === 'string' && payload.title ? payload.title : 'Husly';
  const body = typeof payload.body === 'string' ? payload.body : undefined;
  event.waitUntil(
    self.registration.showNotification(title, { body, data: { url: appPath(payload.url) } }),
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const data = event.notification.data as { url?: unknown } | undefined;
  event.waitUntil(self.clients.openWindow(appPath(data?.url)));
});

export {};

/// <reference lib="webworker" />
// Installable PWA shell (Story 1.1, AD-12). It installs and takes control but caches nothing, so
// it can never serve stale code. Story 3.1 adds the two Web Push handlers (AD-8): show what the
// server sent, and open its link on a tap. Story 3.2 gives each notification a tag, so the day's
// push replaces yesterday's, and a tap focuses an open app window before it opens a new one. It
// is a classic script, so it must stay import-free.
declare const self: ServiceWorkerGlobalScope;

type PushPayload = { title?: unknown; body?: unknown; url?: unknown; tag?: unknown };

const ICON = '/icons/icon-192.png';
const DEFAULT_TAG = 'husly';

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
  const tag = typeof payload.tag === 'string' && payload.tag ? payload.tag : DEFAULT_TAG;
  event.waitUntil(
    // renotify: a new push with the same tag replaces the old one but still alerts.
    self.registration.showNotification(title, {
      body,
      tag,
      icon: ICON,
      badge: ICON,
      data: { url: appPath(payload.url) },
      renotify: true,
    } as NotificationOptions),
  );
});

/** Focus and navigate an open app window; only when there is none (or it will not move) open one. */
async function openApp(path: string): Promise<void> {
  const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
  const own = windows.find((client) => new URL(client.url).origin === self.location.origin);
  if (own) {
    try {
      const focused = await own.focus();
      await focused.navigate(path);
      return;
    } catch {
      // A window the worker does not control cannot be navigated: open a new one instead.
    }
  }
  await self.clients.openWindow(path);
}

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const data = event.notification.data as { url?: unknown } | undefined;
  event.waitUntil(openApp(appPath(data?.url)));
});

export {};

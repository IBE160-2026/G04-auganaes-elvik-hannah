// Story 3.1 (FR-10, AD-8, AD-12, UX-DR31): turning push on for this device. The browser decides
// the permission; the server only stores one PushSubscription per User and device. Components
// reach this through the hooks in queries.ts.
import { api } from './client';
import { GENERIC_ERROR, toApiError } from './errors';

export type PushStatus = 'unsupported' | 'default' | 'granted' | 'denied';

export const PUSH_MESSAGES = {
  title: 'Varsler',
  default: 'Varsler er ikke slått på på denne enheten.',
  granted: 'Varsler er slått på på denne enheten.',
  denied: 'Varsler er blokkert i nettleseren. Tillat dem i nettleserens innstillinger for å få påminnelser.',
  unsupported:
    'Varsler støttes ikke her. På iPhone må du først legge Husly på Hjem-skjermen. I utviklingsmodus er varsler av.',
  enable: 'Slå på varsler',
  retry: 'Prøv igjen',
  failed: 'Vi fikk ikke slått på varsler. Prøv igjen om litt.',
  deniedNote:
    'Du får ikke påminnelser om oppgaver som forfaller, fordi varsler er blokkert i nettleseren. Du kan endre det i nettleserens innstillinger.',
  dismissNote: 'Lukk',
} as const;

// A push request that gets no answer must not hold up signing out.
const SIGN_OUT_TIMEOUT_MS = 3000;

function browserCanPush(): boolean {
  return 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;
}

/** The worker that can subscribe: none in the dev server, which registers no worker (AD-12). */
async function activeRegistration(): Promise<ServiceWorkerRegistration | null> {
  if (!browserCanPush()) return null;
  const registration = await navigator.serviceWorker.getRegistration('/');
  return registration?.active ? registration : null;
}

export async function readPushStatus(): Promise<PushStatus> {
  try {
    if (!(await activeRegistration())) return 'unsupported';
    return Notification.permission;
  } catch {
    // getRegistration can throw (e.g. a SecurityError); Settings must not wait forever.
    return 'unsupported';
  }
}

/** Sync, for the Task Overview note: only an explicit «denied» counts, never «unsupported». */
export function isPushDenied(): boolean {
  return 'Notification' in window && Notification.permission === 'denied';
}

function urlBase64ToBytes(value: string): Uint8Array<ArrayBuffer> {
  const padded = value.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(value.length / 4) * 4, '=');
  const raw = atob(padded);
  return Uint8Array.from(raw, (char) => char.charCodeAt(0));
}

async function fetchPushKey(): Promise<string> {
  const { data, error, response } = await api.GET('/api/push/config');
  if (!data) throw toApiError(response, error, { passThrough: [], fallback: GENERIC_ERROR });
  return data.public_key;
}

/**
 * Subscribes this browser (or reuses its subscription) and tells the server. The server call is
 * idempotent, so this also runs silently on Settings when permission is already granted and
 * this device may not be stored for the signed-in user yet.
 */
export async function registerDevice(): Promise<void> {
  const registration = await activeRegistration();
  if (!registration) throw new Error('Ingen aktiv service worker.');
  const subscription =
    (await registration.pushManager.getSubscription()) ??
    (await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToBytes(await fetchPushKey()),
    }));
  const { endpoint, keys } = subscription.toJSON();
  if (!endpoint || !keys?.p256dh || !keys.auth) throw new Error('Ufullstendig push-abonnement.');
  const { error, response } = await api.PUT('/api/push/subscriptions', {
    body: { endpoint, p256dh: keys.p256dh, auth: keys.auth },
  });
  if (!response.ok) throw toApiError(response, error, { passThrough: [], fallback: GENERIC_ERROR });
}

/** The tap on «Slå på varsler»: asks for permission, and registers the device if it is granted. */
export async function enablePush(): Promise<void> {
  if (!(await activeRegistration())) throw new Error('Ingen aktiv service worker.');
  if ((await Notification.requestPermission()) === 'granted') await registerDevice();
}

/**
 * Sign-out: the server forgets this device, so the next user of a shared browser never gets this
 * user's reminders. A failure is ignored; signing out must never depend on it.
 */
export async function forgetDevice(): Promise<void> {
  try {
    const subscription = await (await activeRegistration())?.pushManager.getSubscription();
    if (!subscription) return;
    await api.DELETE('/api/push/subscriptions', {
      body: { endpoint: subscription.endpoint },
      signal: AbortSignal.timeout(SIGN_OUT_TIMEOUT_MS),
    });
  } catch {
    // Nothing to do: the device row is then removed the next time another user registers it.
  }
}

// The Task Overview note is shown until it is dismissed, once per user and device. localStorage
// can throw (private mode), so every access is guarded; a failure just means «not dismissed».
const NOTE_KEY_PREFIX = 'husly.varselnotatLukket.';

export function readNoteDismissed(userId: string | undefined): boolean {
  if (!userId) return true;
  try {
    return localStorage.getItem(`${NOTE_KEY_PREFIX}${userId}`) !== null;
  } catch {
    return false;
  }
}

export function recordNoteDismissed(userId: string | undefined): void {
  if (!userId) return;
  try {
    localStorage.setItem(`${NOTE_KEY_PREFIX}${userId}`, '1');
  } catch {
    // Not stored: the note comes back on the next visit, which is the safe direction.
  }
}

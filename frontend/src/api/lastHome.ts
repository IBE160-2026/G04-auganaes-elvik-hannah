// Story 2.2 (decisions 3 and 12): the most recently used Home, per user, on this device only.
// localStorage can throw (private mode, blocked storage), so every access is in try/catch and a
// failure just means "no stored Home". The stored id is a hint: pickHome uses it only while the
// Home is still in the server's list, and the next overview visit overwrites it.
import type { Home, Homes } from './homes';

type HomesList = Pick<Homes, 'lived_in_home_id'> & { homes: readonly Home[] };

const KEY_PREFIX = 'husly.sistBrukteHjem.';

export function lastHomeKey(userId: string): string {
  return `${KEY_PREFIX}${userId}`;
}

export function readLastHome(userId: string | undefined): string | null {
  if (!userId) return null;
  try {
    return localStorage.getItem(lastHomeKey(userId));
  } catch {
    return null;
  }
}

/** Called by the Task Overview once its guards pass, never before. */
export function recordLastHome(userId: string | undefined, homeId: string): void {
  if (!userId) return;
  try {
    localStorage.setItem(lastHomeKey(userId), homeId);
  } catch {
    // Not stored; "/" falls back to the Home the user lives in, or the first.
  }
}

/** The Home "/" opens: the stored one if still listed, else lived_in_home_id, else the first. */
export function pickHome(homes: HomesList, storedId: string | null): Home | undefined {
  const find = (id: string | null) => (id ? homes.homes.find((h) => h.id === id) : undefined);
  return find(storedId) ?? find(homes.lived_in_home_id) ?? homes.homes[0];
}

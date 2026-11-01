// Story 1.2 (AD-7): the signed-in session, kept in memory only. Never in localStorage or
// sessionStorage, so a script injected into the page cannot read a stored token.
import { useSyncExternalStore } from 'react';
import type { components } from './schema';

export type User = components['schemas']['UserOut'];
export type Session = { accessToken: string; user: User };

let current: Session | null = null;
const listeners = new Set<() => void>();

export function getSession(): Session | null {
  return current;
}

export function setSession(session: Session | null): void {
  current = session;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** The current session; components re-render when it changes. */
export function useSession(): Session | null {
  return useSyncExternalStore(subscribe, getSession);
}

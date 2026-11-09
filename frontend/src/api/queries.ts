// Story 1.2: TanStack Query hooks, the only way components reach the API (AD-7).
import {
  MutationCache,
  QueryCache,
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
  type Query,
} from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { fetchMe, register, signIn, signOut } from './auth';
import { ApiError } from './errors';
import {
  createHome,
  fetchHomes,
  fetchMembers,
  leaveHome,
  MEMBER_MESSAGES,
  removeMember,
  type Home,
  type Homes,
} from './homes';
import { acceptInvite, createInvite, fetchInvite } from './invites';
import { useSession } from './session';

export function createQueryClient(): QueryClient {
  /**
   * Story 1.8: a 403 from any Home-scoped request means the caller lost access (removed, or
   * left in another tab), or a remove target is already gone. Refetch the Homes and members
   * lists, by prefix since there is no user id here, and let the pages' guards route from the
   * server's answer. The query that failed is left out, so it is never fetched again in a loop.
   */
  function onForbidden(error: Error, failed?: Query<unknown, unknown, unknown>) {
    if (!(error instanceof ApiError && error.status === 403)) return;
    const others = (query: Query) => query !== failed;
    void client.invalidateQueries({ queryKey: ['homes'], predicate: others });
    void client.invalidateQueries({ queryKey: ['members'], predicate: others });
  }

  const client = new QueryClient({
    queryCache: new QueryCache({ onError: (error, query) => onForbidden(error, query) }),
    mutationCache: new MutationCache({ onError: (error) => onForbidden(error) }),
    defaultOptions: {
      // A 401 is already refreshed and retried once by the client middleware.
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return client;
}

export const meKey = ['auth', 'me'] as const;

export function useMe() {
  const session = useSession();
  return useQuery({
    queryKey: [...meKey, session?.user.id],
    queryFn: fetchMe,
    enabled: session !== null,
    initialData: session?.user,
  });
}

export function useSignIn() {
  return useMutation({ mutationFn: signIn });
}

export function useRegister() {
  return useMutation({ mutationFn: register });
}

export function useSignOut() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: signOut,
    onSettled: () => queryClient.clear(),
  });
}

// Story 1.3: keyed on the user, so one user's Homes are never shown to the next.
export function homesKey(userId: string | undefined) {
  return ['homes', userId] as const;
}

export function useHomes() {
  const session = useSession();
  return useQuery({
    queryKey: homesKey(session?.user.id),
    queryFn: fetchHomes,
    enabled: session !== null,
  });
}

// Story 1.5: keyed on the Home and the user. Refetched on mount and window focus, no polling.
export function membersKey(homeId: string, userId: string | undefined) {
  return ['members', homeId, userId] as const;
}

export function useMembers(homeId: string) {
  const session = useSession();
  return useQuery({
    queryKey: membersKey(homeId, session?.user.id),
    queryFn: () => fetchMembers(homeId),
    enabled: session !== null,
  });
}

/**
 * Writes the new Home into the cache before the caller navigates, so "/" never sees the stale
 * empty list and bounces back to Create Home. A refetch then brings the server's allowed_types.
 */
export function useCreateHome() {
  const queryClient = useQueryClient();
  const session = useSession();
  return useMutation({
    mutationFn: createHome,
    onSuccess: (home) => {
      const key = homesKey(session?.user.id);
      queryClient.setQueryData<Homes>(key, (old) => ({
        homes: [home, ...(old?.homes ?? [])],
        // Unknown until the refetch; empty offers nothing the server might refuse.
        allowed_types: [],
      }));
      void queryClient.invalidateQueries({ queryKey: key });
    },
  });
}

// Story 1.4: keyed on the token and the user, so a failed refresh (session gone) refetches
// the preview signed out instead of showing an error.
export function inviteKey(token: string, userId: string | undefined) {
  return ['invite', token, userId] as const;
}

export function useInvite(token: string) {
  const session = useSession();
  return useQuery({
    queryKey: inviteKey(token, session?.user.id),
    queryFn: () => fetchInvite(token),
  });
}

export function useCreateInvite(homeId: string) {
  return useMutation({ mutationFn: () => createInvite(homeId) });
}

/**
 * Like useCreateHome: the joined Home goes first into the cache before the caller navigates,
 * so "/" shows it at once (the server also orders it first) and never bounces.
 */
export function useAcceptInvite(token: string) {
  const queryClient = useQueryClient();
  const session = useSession();
  return useMutation({
    mutationFn: () => acceptInvite(token),
    onSuccess: (home: Home) => {
      const key = homesKey(session?.user.id);
      queryClient.setQueryData<Homes>(key, (old) => ({
        homes: [home, ...(old?.homes ?? []).filter((h) => h.id !== home.id)],
        // Unknown until the refetch; empty offers nothing the server might refuse.
        allowed_types: [],
      }));
      void queryClient.invalidateQueries({ queryKey: key });
      void queryClient.invalidateQueries({ queryKey: ['invite', token] });
    },
  });
}

// Story 1.8: a one-time message for the next page, kept in the query cache (not router state)
// so it survives the guards' redirects ("/hjem/<id>/medlemmer" → "/" → "/nytt-hjem") but not
// a reload.
export function noticeKey(userId: string | undefined) {
  return ['notice', userId] as const;
}

/**
 * The pending notice, taken once. Read in a task after mount, so the persistent aria-live region
 * is in the DOM (empty) before the text arrives and is announced; then removed from the cache,
 * so it is shown only once. StrictMode's first, cleaned-up effect never takes it.
 */
export function useNotice(): string | null {
  const queryClient = useQueryClient();
  const session = useSession();
  const userId = session?.user.id;
  const [notice, setNotice] = useState<string | null>(null);
  useEffect(() => {
    const key = noticeKey(userId);
    const timer = window.setTimeout(() => {
      const pending = queryClient.getQueryData<string>(key);
      if (!pending) return;
      setNotice(pending);
      queryClient.removeQueries({ queryKey: key, exact: true });
    });
    return () => window.clearTimeout(timer);
  }, [queryClient, userId]);
  return notice;
}

/**
 * Leaves the Home, stores «Du har forlatt «X».» for the next page, then waits for the Homes
 * refetch. No navigation and no placeholder: the guards route from the server's answer (to "/",
 * then to Create Home with the server's allowed_types when no Homes remain).
 */
export function useLeaveHome(home: Home) {
  const queryClient = useQueryClient();
  const session = useSession();
  return useMutation({
    mutationFn: () => leaveHome(home.id),
    onSuccess: async () => {
      queryClient.setQueryData(noticeKey(session?.user.id), MEMBER_MESSAGES.leftNotice(home.name));
      await queryClient.refetchQueries({ queryKey: homesKey(session?.user.id) });
    },
  });
}

/** Removes a Tenant, then waits for the members list to refetch without them. */
export function useRemoveMember(homeId: string) {
  const queryClient = useQueryClient();
  const session = useSession();
  return useMutation({
    mutationFn: (userId: string) => removeMember(homeId, userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: membersKey(homeId, session?.user.id) }),
  });
}

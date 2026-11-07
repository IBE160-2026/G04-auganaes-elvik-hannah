// Story 1.2: TanStack Query hooks, the only way components reach the API (AD-7).
import { QueryClient, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchMe, register, signIn, signOut } from './auth';
import { createHome, fetchHomes, type Homes } from './homes';
import { useSession } from './session';

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      // A 401 is already refreshed and retried once by the client middleware.
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
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

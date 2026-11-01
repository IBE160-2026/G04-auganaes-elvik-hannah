// Story 1.2: TanStack Query hooks, the only way components reach the API (AD-7).
import { QueryClient, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchMe, register, signIn, signOut } from './auth';
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

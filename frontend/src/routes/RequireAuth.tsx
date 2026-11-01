import type { ReactNode } from 'react';
import { Navigate } from 'react-router';
import { useSession } from '../api/session';

/** Sends a signed-out visitor to /logg-inn. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const session = useSession();
  if (!session) return <Navigate to="/logg-inn" replace />;
  return children;
}

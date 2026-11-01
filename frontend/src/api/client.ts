// Story 1.2 (AD-7): the one API client. Relative /api paths only (same origin, no CORS).
// Components never call fetch; they use the TanStack Query hooks in queries.ts.
import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from './schema';
import { getSession, setSession } from './session';

/**
 * Endpoints that take credentials or the refresh cookie instead of a Bearer token. A 401 from
 * these is an answer to show (e.g. wrong password), never a reason to refresh and retry.
 */
const CREDENTIAL_PATHS = new Set([
  '/api/auth/register',
  '/api/auth/login',
  '/api/auth/refresh',
  '/api/auth/logout',
]);

// Resolved at call time, so tests can stub globalThis.fetch.
export const api = createClient<paths>({ fetch: (request) => globalThis.fetch(request) });

let inflightRefresh: Promise<boolean> | null = null;

/**
 * Trade the refresh cookie for a new access token. Concurrent callers (several 401s at once,
 * StrictMode's double effect on load) share one request, so the rotated cookie and the token
 * in memory always belong together. Signs out when the cookie is missing or invalid.
 */
export function refreshSession(): Promise<boolean> {
  inflightRefresh ??= (async () => {
    try {
      const { data } = await api.POST('/api/auth/refresh');
      setSession(data ? { accessToken: data.access_token, user: data.user } : null);
      return Boolean(data);
    } catch {
      setSession(null);
      return false;
    } finally {
      inflightRefresh = null;
    }
  })();
  return inflightRefresh;
}

// The untouched request, kept so it can be sent again after a refresh (its body is read once).
const retryCopies = new WeakMap<Request, Request>();

const bearerAuth: Middleware = {
  onRequest({ request, schemaPath }) {
    const session = getSession();
    if (!session || CREDENTIAL_PATHS.has(schemaPath)) return undefined;
    request.headers.set('Authorization', `Bearer ${session.accessToken}`);
    retryCopies.set(request, request.clone());
    return request;
  },
  async onResponse({ request, response }) {
    const copy = retryCopies.get(request);
    if (response.status !== 401 || !copy) return undefined;
    // An expired access token: refresh once, then retry once with the new token.
    if (!(await refreshSession())) return undefined;
    const session = getSession();
    if (!session) return undefined;
    copy.headers.set('Authorization', `Bearer ${session.accessToken}`);
    return globalThis.fetch(copy);
  },
};

api.use(bearerAuth);

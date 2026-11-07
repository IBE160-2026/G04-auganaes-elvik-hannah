// Story 1.2 test helper: stubs globalThis.fetch with handlers per "METHOD /path".
import type { Home, HomeType } from '../api/homes';
import { setSession } from '../api/session';

export type Handler = (request: Request) => Response | Promise<Response>;

export function json(status: number, body?: unknown): Response {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export const OLA = { id: '00000000-0000-4000-8000-000000000001', email: 'ola@example.com', name: 'Ola' };

export function authResponse(accessToken: string, user = OLA) {
  return { access_token: accessToken, token_type: 'bearer', user };
}

/** Installs the handlers; unknown routes answer 404. Returns the list of requests made. */
export function fakeApi(handlers: Record<string, Handler>) {
  const requests: Request[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: Request) => {
      const request = input.clone();
      requests.push(request);
      const handler = handlers[`${input.method} ${new URL(input.url).pathname}`];
      return handler ? handler(input) : json(404, { detail: 'Not Found' });
    }),
  );
  const calls = (method: string, path: string) =>
    requests.filter((r) => r.method === method && new URL(r.url).pathname === path);
  return { requests, calls };
}

export function resetApi() {
  vi.unstubAllGlobals();
  setSession(null);
}

// Story 1.3: Homes as GET /api/homes returns them.
export const OLAS_HOME: Home = {
  id: '00000000-0000-4000-8000-0000000000a1',
  name: 'Kollektivet',
  type: 'household',
  role: 'household_member',
  created_at: '2026-11-07T12:00:00Z',
  can_invite: true,
};

export function homesResponse(homes: readonly Home[] = [OLAS_HOME], allowed_types: HomeType[] = []) {
  return { homes, allowed_types };
}

/** Signed in as Ola on load, with these Homes. */
export function signedInWith(homes: readonly Home[] = [OLAS_HOME], allowed_types: HomeType[] = []) {
  return {
    'POST /api/auth/refresh': () => json(200, authResponse('a1')),
    'GET /api/auth/me': () => json(200, OLA),
    'GET /api/homes': () => json(200, homesResponse(homes, allowed_types)),
  };
}

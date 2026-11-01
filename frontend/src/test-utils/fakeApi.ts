// Story 1.2 test helper: stubs globalThis.fetch with handlers per "METHOD /path".
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

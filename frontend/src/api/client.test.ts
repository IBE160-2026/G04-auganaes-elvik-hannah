// Story 1.2 (AD-7): refresh-and-retry on 401, shared refresh, no refresh on credential 401s.
import { signIn } from './auth';
import { api, refreshSession } from './client';
import { getSession, setSession } from './session';
import { OLA, authResponse, fakeApi, json, resetApi } from '../test-utils/fakeApi';

afterEach(resetApi);

function bearer(request: Request) {
  return request.headers.get('Authorization');
}

describe('API client', () => {
  it('adds the access token as Bearer', async () => {
    setSession({ accessToken: 'a1', user: OLA });
    const server = fakeApi({ 'GET /api/auth/me': () => json(200, OLA) });

    await api.GET('/api/auth/me');

    expect(bearer(server.calls('GET', '/api/auth/me')[0])).toBe('Bearer a1');
  });

  it('refreshes once and retries once with the new token after a 401', async () => {
    setSession({ accessToken: 'expired', user: OLA });
    const server = fakeApi({
      'GET /api/auth/me': (request) =>
        bearer(request) === 'Bearer fresh' ? json(200, OLA) : json(401, { detail: 'x' }),
      'POST /api/auth/refresh': () => json(200, authResponse('fresh')),
    });

    const { data } = await api.GET('/api/auth/me');

    expect(data).toEqual(OLA);
    expect(server.calls('POST', '/api/auth/refresh')).toHaveLength(1);
    expect(server.calls('GET', '/api/auth/me').map(bearer)).toEqual(['Bearer expired', 'Bearer fresh']);
    expect(getSession()?.accessToken).toBe('fresh');
  });

  it('shares one refresh between concurrent 401s', async () => {
    setSession({ accessToken: 'expired', user: OLA });
    const server = fakeApi({
      'GET /api/auth/me': (request) =>
        bearer(request) === 'Bearer fresh' ? json(200, OLA) : json(401, { detail: 'x' }),
      'POST /api/auth/refresh': async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return json(200, authResponse('fresh'));
      },
    });

    const results = await Promise.all([api.GET('/api/auth/me'), api.GET('/api/auth/me'), api.GET('/api/auth/me')]);

    expect(results.map((r) => r.data)).toEqual([OLA, OLA, OLA]);
    expect(server.calls('POST', '/api/auth/refresh')).toHaveLength(1);
  });

  it('does not retry again when the retry also gets a 401', async () => {
    setSession({ accessToken: 'expired', user: OLA });
    const server = fakeApi({
      'GET /api/auth/me': () => json(401, { detail: 'x' }),
      'POST /api/auth/refresh': () => json(200, authResponse('fresh')),
    });

    const { response } = await api.GET('/api/auth/me');

    expect(response.status).toBe(401);
    expect(server.calls('GET', '/api/auth/me')).toHaveLength(2);
    expect(server.calls('POST', '/api/auth/refresh')).toHaveLength(1);
  });

  it('signs out when the refresh fails', async () => {
    setSession({ accessToken: 'expired', user: OLA });
    fakeApi({
      'GET /api/auth/me': () => json(401, { detail: 'x' }),
      'POST /api/auth/refresh': () => json(401, { detail: 'Økten er utløpt.' }),
    });

    const { response } = await api.GET('/api/auth/me');

    expect(response.status).toBe(401);
    expect(getSession()).toBeNull();
  });

  it('signs out when the refresh request itself fails (offline)', async () => {
    setSession({ accessToken: 'a1', user: OLA });
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));

    expect(await refreshSession()).toBe(false);
    expect(getSession()).toBeNull();
  });

  it('makes no refresh call when login answers 401 (wrong password)', async () => {
    const server = fakeApi({
      'POST /api/auth/login': () => json(401, { detail: 'Feil e-post eller passord.' }),
    });

    await expect(signIn({ email: OLA.email, password: 'feilfeil' })).rejects.toThrow(
      'Feil e-post eller passord.',
    );
    expect(server.calls('POST', '/api/auth/refresh')).toHaveLength(0);
  });

  it('sends no Bearer to the credential endpoints, even when signed in', async () => {
    setSession({ accessToken: 'a1', user: OLA });
    const server = fakeApi({ 'POST /api/auth/refresh': () => json(401, { detail: 'x' }) });

    await refreshSession();

    expect(bearer(server.calls('POST', '/api/auth/refresh')[0])).toBeNull();
    expect(server.calls('POST', '/api/auth/refresh')).toHaveLength(1);
  });

  it('keeps no token in Web Storage after signing in', async () => {
    fakeApi({ 'POST /api/auth/login': () => json(200, authResponse('secret-token')) });

    await signIn({ email: OLA.email, password: 'hemmelig1' });

    expect(getSession()?.accessToken).toBe('secret-token');
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it('calls only relative same-origin /api paths', async () => {
    const server = fakeApi({ 'POST /api/auth/refresh': () => json(401, { detail: 'x' }) });

    await refreshSession();

    expect(new URL(server.requests[0].url).origin).toBe(window.location.origin);
  });
});

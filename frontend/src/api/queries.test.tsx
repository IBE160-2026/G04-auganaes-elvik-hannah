// Story 2.4: which failed ticks are retried quietly (useCompleteTask's retry rule).
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { OLA, OLAS_HOME, OLAS_TENANCY, fakeApi, homesResponse, json, resetApi } from '../test-utils/fakeApi';
import { ApiError } from './errors';
import { homesKey, inviteKey, isTransient, membersKey, portfolioKey, tasksKey, useHomes } from './queries';
import { setSession } from './session';

describe('isTransient', () => {
  it('retries a network error', () => {
    expect(isTransient(new TypeError('Failed to fetch'))).toBe(true);
  });

  it.each([500, 502, 408, 429])('retries %i', (status) => {
    expect(isTransient(new ApiError(status, 'x'))).toBe(true);
  });

  it.each([404, 422, 403])('does not retry %i', (status) => {
    expect(isTransient(new ApiError(status, 'x'))).toBe(false);
  });
});

// Story 1.5 follow-up (deferred-work): the user id is in every key that holds one user's data, so
// a session change to another user without a sign-out never shows the previous user's cache.
describe('the user id in the query keys', () => {
  it.each([
    ['homesKey', (id: string) => homesKey(id)],
    ['membersKey', (id: string) => membersKey('home-1', id)],
    ['inviteKey', (id: string) => inviteKey('token-1', id)],
    ['tasksKey', (id: string) => tasksKey('home-1', id)],
    ['portfolioKey', (id: string) => portfolioKey(id)],
  ])('%s differs between two users', (_name, keyFor) => {
    // Guards the user id in each key function.
    expect(keyFor('user-a')).not.toEqual(keyFor('user-b'));
  });

  it('shows another user a fresh load, never the previous user’s Homes, after a session change', async () => {
    const client = new QueryClient();
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
    fakeApi({
      'GET /api/homes': (request) =>
        json(200, homesResponse(request.headers.get('Authorization') === 'Bearer a1' ? [OLAS_HOME] : [OLAS_TENANCY])),
    });
    setSession({ accessToken: 'a1', user: OLA });
    const { result } = renderHook(() => useHomes(), { wrapper });
    await waitFor(() => expect(result.current.data?.homes[0].name).toBe(OLAS_HOME.name));

    act(() => setSession({ accessToken: 'b1', user: { ...OLA, id: 'user-b' } }));

    // Guards homesKey(session?.user.id): without the id the cache of user A answers at once.
    expect(result.current.data).toBeUndefined();
    await waitFor(() => expect(result.current.data?.homes[0].name).toBe(OLAS_TENANCY.name));
    resetApi();
    setSession(null);
  });
});

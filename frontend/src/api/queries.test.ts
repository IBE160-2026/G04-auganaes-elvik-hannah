// Story 2.4: which failed ticks are retried quietly (useCompleteTask's retry rule).
import { ApiError } from './errors';
import { isTransient } from './queries';

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

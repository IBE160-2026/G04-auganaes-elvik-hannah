// Epic 1 retro, action 2 (A1): which server reasons reach the user, per pass-through rule.
import { MESSAGES } from './auth';
import { ApiError, fieldsOf, toApiError, type ToApiErrorOptions } from './errors';
import { HOME_MESSAGES, MEMBER_MESSAGES } from './homes';
import { INVITE_MESSAGES } from './invites';

const FALLBACK = 'Reservetekst.';
const REASON = 'Serverens grunn.';
const VALIDATION = [{ loc: ['body', 'name'], msg: 'x', type: 'missing' }];

function response(status: number): Response {
  return new Response(null, { status });
}

function convert(status: number, body: unknown, options: Partial<ToApiErrorOptions> = {}): ApiError {
  return toApiError(response(status), body, { passThrough: 'any', fallback: FALLBACK, ...options });
}

describe('toApiError', () => {
  it.each([
    ['any', 'any', 401, REASON],
    ['any', 'any', 409, REASON],
    ['any', 'any', 500, REASON],
    ['[409]', [409], 409, REASON],
    ['[409]', [409], 410, FALLBACK],
    ['[409]', [409], 500, FALLBACK],
    ['[409, 410]', [409, 410], 409, REASON],
    ['[409, 410]', [409, 410], 410, REASON],
    ['[409, 410]', [409, 410], 500, FALLBACK],
  ] as const)(
    'passThrough %s on a %i with a string detail gives the right message',
    (_, passThrough, status, message) => {
      const error = convert(status, { detail: REASON }, { passThrough });

      expect(error).toBeInstanceOf(ApiError);
      expect(error.name).toBe('ApiError');
      expect(error.status).toBe(status);
      expect(error.message).toBe(message);
      expect(error.fields).toEqual({});
    },
  );

  it('maps a 422 with a detail list through the fields mapper, with the fallback as message', () => {
    const fields = vi.fn(() => ({ name: 'Gi hjemmet et navn.' }));

    const error = convert(422, { detail: VALIDATION }, { passThrough: [409], fields });

    expect(fields).toHaveBeenCalledWith(VALIDATION);
    expect(error.status).toBe(422);
    expect(error.message).toBe(FALLBACK);
    expect(fieldsOf<{ name?: string }>(error)).toEqual({ name: 'Gi hjemmet et navn.' });
  });

  it('treats a 422 like any other status without a fields mapper', () => {
    expect(convert(422, { detail: VALIDATION }, { passThrough: [409, 410] }).message).toBe(FALLBACK);
    expect(convert(422, { detail: VALIDATION }, { passThrough: [409, 410] }).fields).toEqual({});
    expect(convert(422, { detail: REASON }, { passThrough: 'any' }).message).toBe(REASON);
  });

  it('uses the fallback for a non-string detail', () => {
    expect(convert(409, { detail: { reason: REASON } }).message).toBe(FALLBACK);
    expect(convert(409, { detail: ['a'] }, { passThrough: [409] }).message).toBe(FALLBACK);
  });

  it('uses the fallback when there is no body', () => {
    expect(convert(500, undefined).message).toBe(FALLBACK);
    expect(convert(502, null, { passThrough: [409] }).message).toBe(FALLBACK);
    expect(convert(409, {}, { passThrough: [409] }).message).toBe(FALLBACK);
  });

  it('runs a 422 with a string detail through the pass-through rule, even with a fields mapper', () => {
    const fields = vi.fn(() => ({ name: 'x' }));

    const any = convert(422, { detail: REASON }, { passThrough: 'any', fields });
    const only409 = convert(422, { detail: REASON }, { passThrough: [409], fields });

    expect(fields).not.toHaveBeenCalled();
    expect([any.message, any.fields]).toEqual([REASON, {}]);
    expect([only409.message, only409.fields]).toEqual([FALLBACK, {}]);
  });
});

describe('the messages the forms already show', () => {
  it('keep the generic text and the members load message', () => {
    for (const unknown of [MESSAGES.unknown, HOME_MESSAGES.unknown, INVITE_MESSAGES.unknown]) {
      expect(unknown).toBe('Noe gikk galt. Prøv igjen om litt.');
    }
    expect(MEMBER_MESSAGES.loadFailed).toBe('Vi fikk ikke hentet medlemmene.');
  });
});

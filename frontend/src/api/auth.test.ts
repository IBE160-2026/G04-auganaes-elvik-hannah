// Story 1.2 (FR-1): client-side checks and 422 mapping give the same Norwegian messages.
import { MESSAGES, fieldErrorsFrom422, validateRegister, validateSignIn } from './auth';

const VALID = { email: 'ola@example.com', name: 'Ola', password: 'hemmelig1' };

describe('validateRegister', () => {
  it('accepts valid input and the boundaries', () => {
    expect(validateRegister(VALID)).toEqual({});
    expect(validateRegister({ ...VALID, password: 'a'.repeat(8), name: 'a'.repeat(50) })).toEqual({});
    expect(validateRegister({ ...VALID, password: 'a'.repeat(128) })).toEqual({});
  });

  it.each([
    [{ email: '' }, 'email', MESSAGES.emailMissing],
    [{ email: 'ikke-epost' }, 'email', MESSAGES.emailInvalid],
    [{ name: '   ' }, 'name', MESSAGES.nameMissing],
    [{ name: 'a'.repeat(51) }, 'name', MESSAGES.nameTooLong],
    [{ password: 'a'.repeat(7) }, 'password', MESSAGES.passwordTooShort],
    [{ password: 'a'.repeat(129) }, 'password', MESSAGES.passwordTooLong],
  ])('%o gives an error on %s', (override, field, message) => {
    expect(validateRegister({ ...VALID, ...override })).toEqual({ [field]: message });
  });
});

describe('validateSignIn', () => {
  it('only requires both fields', () => {
    expect(validateSignIn({ email: 'x', password: 'y' })).toEqual({});
    expect(validateSignIn({ email: '', password: '' })).toEqual({
      email: MESSAGES.emailMissing,
      password: MESSAGES.passwordMissing,
    });
  });
});

describe('fieldErrorsFrom422', () => {
  it('maps FastAPI errors by loc to Norwegian messages', () => {
    expect(
      fieldErrorsFrom422([
        { loc: ['body', 'email'], msg: 'value is not a valid email address', type: 'value_error' },
        { loc: ['body', 'name'], msg: 'String should have at most 50 characters', type: 'string_too_long' },
        { loc: ['body', 'password'], msg: 'String should have at least 8 characters', type: 'string_too_short' },
      ]),
    ).toEqual({
      email: MESSAGES.emailInvalid,
      name: MESSAGES.nameTooLong,
      password: MESSAGES.passwordTooShort,
    });
  });

  it('ignores unknown locations and keeps the first error per field', () => {
    expect(
      fieldErrorsFrom422([
        { loc: ['body'], msg: 'x', type: 'missing' },
        { loc: ['body', 'password'], msg: 'x', type: 'string_too_long' },
        { loc: ['body', 'password'], msg: 'x', type: 'string_too_short' },
      ]),
    ).toEqual({ password: MESSAGES.passwordTooLong });
  });
});

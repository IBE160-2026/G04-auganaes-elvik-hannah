// Story 1.2 (FR-1): sign in, register and sign out, with errors turned into Norwegian copy.
import { api } from './client';
import { GENERIC_ERROR, toApiError } from './errors';
import type { components } from './schema';
import { setSession } from './session';

type AuthResponse = components['schemas']['AuthResponse'];
type RegisterResponse = components['schemas']['RegisterResponse'];
type ValidationError = components['schemas']['ValidationError'];

export type Field = 'email' | 'name' | 'password';
export type FieldErrors = Partial<Record<Field, string>>;
export type RegisterInput = { email: string; name: string; password: string };
/** Story 1.4: registering through an invite link joins its Home in the same request. */
export type RegisterRequest = RegisterInput & { invite_token?: string };
export type SignInInput = { email: string; password: string };

// Same limits as backend/app/routes/auth.py.
export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 128;
export const NAME_MAX = 50;

export const MESSAGES = {
  emailInvalid: 'Skriv inn en gyldig e-postadresse, for eksempel navn@eksempel.no.',
  emailMissing: 'Skriv inn e-postadressen din.',
  nameMissing: 'Skriv inn navnet ditt.',
  nameTooLong: `Navnet kan ha maks ${NAME_MAX} tegn.`,
  passwordMissing: 'Skriv inn passordet ditt.',
  passwordTooShort: `Passordet må ha minst ${PASSWORD_MIN} tegn.`,
  passwordTooLong: `Passordet kan ha maks ${PASSWORD_MAX} tegn.`,
  unknown: GENERIC_ERROR,
} as const;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Length in code points, as Pydantic counts it (an emoji is 1, not 2 UTF-16 units). */
function length(value: string): number {
  return [...value].length;
}

/** Client-side checks, mirroring the server's 422 rules. */
export function validateRegister({ email, name, password }: RegisterInput): FieldErrors {
  const errors: FieldErrors = {};
  if (!email.trim()) errors.email = MESSAGES.emailMissing;
  else if (!EMAIL_PATTERN.test(email.trim())) errors.email = MESSAGES.emailInvalid;
  if (!name.trim()) errors.name = MESSAGES.nameMissing;
  else if (length(name.trim()) > NAME_MAX) errors.name = MESSAGES.nameTooLong;
  if (length(password) < PASSWORD_MIN) errors.password = MESSAGES.passwordTooShort;
  else if (length(password) > PASSWORD_MAX) errors.password = MESSAGES.passwordTooLong;
  return errors;
}

export function validateSignIn({ email, password }: SignInInput): FieldErrors {
  const errors: FieldErrors = {};
  if (!email.trim()) errors.email = MESSAGES.emailMissing;
  if (!password) errors.password = MESSAGES.passwordMissing;
  return errors;
}

function messageFor(field: Field, error: ValidationError): string {
  if (field === 'email') return MESSAGES.emailInvalid;
  if (field === 'name') return error.type === 'string_too_long' ? MESSAGES.nameTooLong : MESSAGES.nameMissing;
  return error.type === 'string_too_long' ? MESSAGES.passwordTooLong : MESSAGES.passwordTooShort;
}

/** FastAPI's 422 body → one Norwegian message per field, found by `loc` ["body", field]. */
export function fieldErrorsFrom422(detail: ValidationError[] | undefined): FieldErrors {
  const errors: FieldErrors = {};
  for (const error of detail ?? []) {
    const field = error.loc[1];
    if ((field === 'email' || field === 'name' || field === 'password') && !errors[field]) {
      errors[field] = messageFor(field, error);
    }
  }
  return errors;
}

/** Any string reason from the server is shown (wrong password, email taken, expired session). */
function toAuthError(response: Response, error: unknown) {
  return toApiError(response, error, {
    passThrough: 'any',
    fallback: MESSAGES.unknown,
    fields: fieldErrorsFrom422,
  });
}

function signedIn<T extends AuthResponse>(data: T): T {
  setSession({ accessToken: data.access_token, user: data.user });
  return data;
}

export async function signIn(body: SignInInput): Promise<AuthResponse> {
  const { data, error, response } = await api.POST('/api/auth/login', { body });
  if (!data) throw toAuthError(response, error);
  return signedIn(data);
}

export async function register(body: RegisterRequest): Promise<RegisterResponse> {
  const { data, error, response } = await api.POST('/api/auth/register', { body });
  if (!data) throw toAuthError(response, error);
  return signedIn(data);
}

/** Clears the refresh cookie on the server; the frontend is signed out even if that fails. */
export async function signOut(): Promise<void> {
  try {
    await api.POST('/api/auth/logout');
  } finally {
    setSession(null);
  }
}

export async function fetchMe() {
  const { data, error, response } = await api.GET('/api/auth/me');
  if (!data) throw toAuthError(response, error);
  return data;
}

// Epic 1 retro, action 2 (A1): one way to turn a failed API call into a Norwegian message,
// shared by auth, homes and invites (FR-1, FR-2, FR-3).
import type { components } from './schema';

type ValidationError = components['schemas']['ValidationError'];

export type FieldMessages = Partial<Record<string, string>>;

export const GENERIC_ERROR = 'Noe gikk galt. Prøv igjen om litt.';

/** A failed API call. `message` is for the form; `fields` holds messages per input after a 422. */
export class ApiError extends Error {
  readonly status: number;
  readonly fields: FieldMessages;

  constructor(status: number, message: string, fields: FieldMessages = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fields = fields;
  }
}

export type ToApiErrorOptions = {
  /** Statuses whose string `detail` (the server's Norwegian reason) is shown; 'any' for all. */
  passThrough: 'any' | readonly number[];
  /** The message when the server's reason is not passed through. */
  fallback: string;
  /** Maps FastAPI's 422 `detail` to messages per input. Without it a 422 is handled like any status. */
  fields?: (detail: ValidationError[]) => FieldMessages;
};

export function toApiError(response: Response, error: unknown, options: ToApiErrorOptions): ApiError {
  const { passThrough, fallback, fields } = options;
  const body = (error ?? {}) as { detail?: unknown };
  if (fields && response.status === 422 && Array.isArray(body.detail)) {
    return new ApiError(422, fallback, fields(body.detail as ValidationError[]));
  }
  const passes = passThrough === 'any' || passThrough.includes(response.status);
  const message = passes && typeof body.detail === 'string' ? body.detail : fallback;
  return new ApiError(response.status, message);
}

/**
 * The field messages of a failed call, typed for the form that owns those fields. This is a
 * cast, not a runtime check: it trusts the calling module's 422 mapper to produce only that
 * form's fields.
 */
export function fieldsOf<F extends FieldMessages>(error: ApiError): F {
  return error.fields as F;
}

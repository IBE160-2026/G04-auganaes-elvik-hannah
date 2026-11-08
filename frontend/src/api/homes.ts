// Story 1.3 (FR-1, FR-3): list and create the signed-in user's Homes, with Norwegian errors.
// Story 1.5 (FR-3): the Members of one Home.
import { api } from './client';
import { ApiError, GENERIC_ERROR, toApiError } from './errors';
import type { components } from './schema';

export type Home = components['schemas']['HomeOut'];
export type Homes = components['schemas']['HomesOut'];
export type HomeType = Home['type'];
export type Role = Home['role'];
export type CreateHomeInput = components['schemas']['CreateHomeRequest'];
export type Member = components['schemas']['MemberOut'];

type ValidationError = components['schemas']['ValidationError'];

export type HomeField = 'name' | 'type';
export type HomeFieldErrors = Partial<Record<HomeField, string>>;

// Same limit as backend/app/models/home.py.
export const HOME_NAME_MAX = 60;

export const HOME_MESSAGES = {
  nameMissing: 'Gi hjemmet et navn.',
  nameTooLong: `Navnet kan ha maks ${HOME_NAME_MAX} tegn.`,
  typeMissing: 'Velg hva slags hjem dette er.',
  loadFailed: 'Vi fikk ikke hentet hjemmene dine.',
  unknown: GENERIC_ERROR,
} as const;

export const MEMBER_MESSAGES = {
  loadFailed: 'Vi fikk ikke hentet medlemmene.',
} as const;

export const TYPE_LABELS: Record<HomeType, string> = {
  household: 'Husstand',
  landlord: 'Utleiebolig',
};

export const ROLE_LABELS: Record<Role, string> = {
  household_member: 'Husstandsmedlem',
  landlord: 'Utleier',
  tenant: 'Leietaker',
};

/** Client-side checks, mirroring the server's 422 rules. `type` is null until one is chosen. */
export function validateCreateHome(name: string, type: HomeType | null): HomeFieldErrors {
  const errors: HomeFieldErrors = {};
  const trimmed = name.trim();
  if (!trimmed) errors.name = HOME_MESSAGES.nameMissing;
  // Code points, as Pydantic counts them.
  else if ([...trimmed].length > HOME_NAME_MAX) errors.name = HOME_MESSAGES.nameTooLong;
  if (!type) errors.type = HOME_MESSAGES.typeMissing;
  return errors;
}

function fieldErrorsFrom422(detail: ValidationError[]): HomeFieldErrors {
  const errors: HomeFieldErrors = {};
  for (const error of detail) {
    const field = error.loc[1];
    if (field === 'name' && !errors.name) {
      errors.name = error.type === 'string_too_long' ? HOME_MESSAGES.nameTooLong : HOME_MESSAGES.nameMissing;
    } else if (field === 'type' && !errors.type) {
      errors.type = HOME_MESSAGES.typeMissing;
    }
  }
  return errors;
}

/** A 409 carries the server's Norwegian reason; anything else gets the generic message. */
function toHomeError(response: Response, error: unknown) {
  return toApiError(response, error, {
    passThrough: [409],
    fallback: HOME_MESSAGES.unknown,
    fields: fieldErrorsFrom422,
  });
}

export async function fetchHomes(): Promise<Homes> {
  const { data, error, response } = await api.GET('/api/homes');
  if (!data) throw toHomeError(response, error);
  return data;
}

export async function createHome(body: CreateHomeInput): Promise<Home> {
  const { data, error, response } = await api.POST('/api/homes', { body });
  if (!data) throw toHomeError(response, error);
  return data;
}

/** Every Member of the Home, the Landlord first. Any failure gets the one load message. */
export async function fetchMembers(homeId: string): Promise<Member[]> {
  const { data, response } = await api.GET('/api/homes/{home_id}/members', {
    params: { path: { home_id: homeId } },
  });
  if (!data) throw new ApiError(response.status, MEMBER_MESSAGES.loadFailed);
  return data.members;
}

// Story 1.4 (FR-2): create, preview and accept invite links, with errors in Norwegian.
import { api } from './client';
import { GENERIC_ERROR, toApiError } from './errors';
import type { HomeType } from './homes';
import type { components } from './schema';

export type Invite = components['schemas']['InviteOut'];
export type InvitePreview = components['schemas']['InvitePreviewOut'];

/** A raw token from a URL. Anything else is ignored, never sent or put in a redirect. */
const TOKEN_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;

export function validInviteToken(value: string | null | undefined): string | null {
  return value && TOKEN_PATTERN.test(value) ? value : null;
}

/** The full link to share, on whatever origin the app runs (localhost, preview, production). */
export function inviteUrl(token: string): string {
  return `${window.location.origin}/invitasjon/${token}`;
}

const ASK_WHOM: Record<HomeType, string> = {
  landlord: 'utleieren',
  household: 'et husstandsmedlem',
};

/** Same copy as backend/app/routes/invites.py; null home type means an unknown token. */
export function invalidInviteMessage(homeType: HomeType | null | undefined): string {
  const whom = homeType ? ASK_WHOM[homeType] : 'den som inviterte deg';
  return `Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra ${whom}.`;
}

export const INVITE_MESSAGES = {
  createFailed: 'Vi fikk ikke laget en invitasjonslenke.',
  loadFailed: 'Vi fikk ikke hentet invitasjonen.',
  unknown: GENERIC_ERROR,
} as const;

/** A 409 or 410 carries the server's Norwegian reason; anything else gets `fallback`. */
function toInviteError(response: Response, error: unknown, fallback: string) {
  return toApiError(response, error, { passThrough: [409, 410], fallback });
}

export async function createInvite(homeId: string): Promise<Invite> {
  const { data, error, response } = await api.POST('/api/homes/{home_id}/invites', {
    params: { path: { home_id: homeId } },
  });
  if (!data) throw toInviteError(response, error, INVITE_MESSAGES.createFailed);
  return data;
}

export async function fetchInvite(token: string): Promise<InvitePreview> {
  const { data, error, response } = await api.GET('/api/invites/{token}', {
    params: { path: { token } },
  });
  if (!data) throw toInviteError(response, error, INVITE_MESSAGES.loadFailed);
  return data;
}

export async function acceptInvite(token: string) {
  const { data, error, response } = await api.POST('/api/invites/{token}/accept', {
    params: { path: { token } },
  });
  if (!data) throw toInviteError(response, error, INVITE_MESSAGES.unknown);
  return data;
}

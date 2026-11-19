// Story 3.4 (FR-12): the Landlord's message to a Home's Tenants, with Norwegian copy.
import { api } from './client';
import { GENERIC_ERROR, toApiError } from './errors';
import type { components } from './schema';

export type BroadcastResult = components['schemas']['BroadcastOut'];

// Same limit as backend/app/domain/broadcast.py.
export const BROADCAST_MAX = 300;

export const BROADCAST_MESSAGES = {
  empty: 'Skriv en melding først.',
  tooLong: `Meldingen kan ha maks ${BROADCAST_MAX} tegn.`,
  failed: 'Vi fikk ikke sendt meldingen. Prøv igjen.',
  unknown: GENERIC_ERROR,
} as const;

/** Names nobody (UX-DR12): only how many Tenants took the push, and how many could not. */
export function sentNotice(result: BroadcastResult): string {
  const sent = `Sendt til ${result.recipients} ${result.recipients === 1 ? 'leietaker' : 'leietakere'}.`;
  if (result.without_push === 0) return sent;
  const rest =
    result.without_push === 1
      ? '1 har ikke slått på varsler.'
      : `${result.without_push} har ikke slått på varsler.`;
  return `${sent} ${rest}`;
}

/** Client-side check, mirroring the server's 422 rules. Code points, as Pydantic counts them. */
export function validateBroadcast(text: string): string | null {
  const trimmed = text.trim();
  if (!trimmed) return BROADCAST_MESSAGES.empty;
  if ([...trimmed].length > BROADCAST_MAX) return BROADCAST_MESSAGES.tooLong;
  return null;
}

export async function sendBroadcast(homeId: string, message: string): Promise<BroadcastResult> {
  const { data, error, response } = await api.POST('/api/homes/{home_id}/broadcast', {
    params: { path: { home_id: homeId } },
    body: { message },
  });
  // A 409 carries the server's Norwegian reason (no Tenants yet); anything else gets the fallback.
  if (!data) throw toApiError(response, error, { passThrough: [409], fallback: BROADCAST_MESSAGES.failed });
  return data;
}

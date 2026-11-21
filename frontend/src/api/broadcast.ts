// Story 3.4 (FR-12): the Landlord's message to a Home's Tenants, with Norwegian copy.
import { api } from './client';
import { toApiError } from './errors';
import type { components } from './schema';

export type BroadcastResult = components['schemas']['BroadcastOut'];

// Same limit as backend/app/domain/broadcast.py.
export const BROADCAST_MAX = 300;

export const BROADCAST_MESSAGES = {
  empty: 'Skriv en melding først.',
  tooLong: `Meldingen kan ha maks ${BROADCAST_MAX} tegn.`,
  failed: 'Vi fikk ikke sendt meldingen. Prøv igjen.',
  // The mock sender is active (no VAPID keys on the server): nothing reached a device.
  demo: 'Demo: ingen ekte varsler er sendt.',
} as const;

/**
 * Names nobody (UX-DR12): only how many Tenants took the push, and how many could not be
 * reached (no device, or every send failed). Nobody reached is not «Sendt».
 */
export function sentNotice(result: BroadcastResult): string {
  const demo = result.demo ? ` ${BROADCAST_MESSAGES.demo}` : '';
  if (result.recipients === 0) {
    return 'Ingen leietakere kunne nås med varsel. Teksten er beholdt, så du kan prøve igjen.';
  }
  const sent = `Sendt til ${result.recipients} ${result.recipients === 1 ? 'leietaker' : 'leietakere'}.`;
  if (result.without_push === 0) return `${sent}${demo}`;
  return `${sent} ${result.without_push} kunne ikke nås med varsel.${demo}`;
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

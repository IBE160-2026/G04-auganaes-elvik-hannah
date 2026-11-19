// Story 3.5 (FR-13): the Landlord's reminder cadence for a Home's Tenants, with Norwegian copy.
import { api } from './client';
import { toApiError } from './errors';

// Same options as backend/app/models/home.py (CADENCE_OPTIONS); the server refuses anything else.
export const CADENCE_OPTIONS = [
  { days: 1, label: 'Hver dag' },
  { days: 2, label: 'Annenhver dag' },
  { days: 7, label: 'Én gang i uken' },
] as const;

export const CADENCE_MESSAGES = {
  failed: 'Vi fikk ikke lagret påminnelsene. Prøv igjen.',
  saved: 'Lagret.',
} as const;

export async function saveCadence(homeId: string, days: number): Promise<number> {
  const { data, error, response } = await api.PUT('/api/homes/{home_id}/notification-cadence', {
    params: { path: { home_id: homeId } },
    // The type is the three literals; the radio group only offers those.
    body: { days: days as 1 | 2 | 7 },
  });
  if (!data) throw toApiError(response, error, { passThrough: [], fallback: CADENCE_MESSAGES.failed });
  return data.notification_cadence_days;
}

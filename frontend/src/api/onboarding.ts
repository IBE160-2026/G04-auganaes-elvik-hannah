// Story 5.3 (FR-16, AD-4): the onboarding guide of a Landlord Home. The introduction was written
// once by the server's AI service; the Home's name and its Must tasks come live with it. The
// disclaimer arrives in its own field and is shown whenever an AI wrote the introduction.
import { api } from './client';
import { GENERIC_ERROR, toApiError } from './errors';
import type { components } from './schema';

export type Guide = components['schemas']['GuideOut'];

export const GUIDE_MESSAGES = {
  title: 'Velkomstguide',
  heading: (homeName: string) => `Velkommen til ${homeName}`,
  mustHeading: 'Dette er de viktigste oppgavene (Må)',
  noMust: 'Det er ingen Må-oppgaver i hjemmet akkurat nå.',
  dismiss: 'Skjul',
  dismissFailed: 'Vi fikk ikke skjult guiden. Prøv igjen.',
  readAgain: 'Du finner guiden igjen under Innstillinger.',
  loadFailed: 'Vi fikk ikke hentet guiden. Prøv igjen.',
  backToHome: 'Tilbake til oppgavene',
  demo: 'Demo-tekst: ingen KI-nøkkel er satt, så denne velkomsten er ferdigskrevet.',
} as const;

export async function fetchGuide(homeId: string): Promise<Guide> {
  const { data, error, response } = await api.GET('/api/homes/{home_id}/onboarding-guide', {
    params: { path: { home_id: homeId } },
  });
  if (!data) throw toApiError(response, error, { passThrough: [404], fallback: GENERIC_ERROR });
  return data;
}

export async function dismissGuide(homeId: string): Promise<void> {
  const { error, response } = await api.POST('/api/homes/{home_id}/onboarding-guide/dismiss', {
    params: { path: { home_id: homeId } },
  });
  if (!response.ok) {
    throw toApiError(response, error, { passThrough: [], fallback: GUIDE_MESSAGES.dismissFailed });
  }
}

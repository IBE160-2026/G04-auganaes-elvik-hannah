// Story 6.1 (FR-20): the Landlord's Portfolio, one row per Landlord Home. The server decides the
// status (domain/portfolio); this file only fetches it and holds the words.
import { api } from './client';
import { ApiError } from './errors';
import type { components } from './schema';

export type Portfolio = components['schemas']['PortfolioOut'];
export type PortfolioHome = components['schemas']['PortfolioHomeOut'];
export type PortfolioStatus = PortfolioHome['status'];

// The text carries the status; the colour only reinforces it.
export const STATUS_LABELS: Record<PortfolioStatus, string> = {
  behind: 'Forsinket',
  on_track: 'Alt i orden',
  not_set_up: 'Ikke satt opp',
};

export const PORTFOLIO_MESSAGES = {
  loadFailed: 'Vi fikk ikke hentet porteføljen.',
  refreshed: 'Oppdatert',
  refreshFailed: 'Vi fikk ikke oppdatert porteføljen.',
  noOverdue: 'Ingen forfalte Må-oppgaver.',
} as const;

export function overdueCountText(count: number): string {
  return count === 1 ? '1 forfalt Må-oppgave' : `${count} forfalte Må-oppgaver`;
}

export function daysOverdueText(days: number): string {
  return days === 1 ? '1 dag forsinket' : `${days} dager forsinket`;
}

export function dueSoonText(count: number): string {
  return count === 1 ? '1 Må-oppgave snart forfalt' : `${count} Må-oppgaver snart forfalt`;
}

export async function fetchPortfolio(): Promise<Portfolio> {
  const { data, response } = await api.GET('/api/portfolio');
  if (!data) throw new ApiError(response.status, PORTFOLIO_MESSAGES.loadFailed);
  return data;
}

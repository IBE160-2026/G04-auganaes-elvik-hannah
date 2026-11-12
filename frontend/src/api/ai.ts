// Story 5.1 (FR-14, AD-4): «?» on a Task. The server's AI service answers; React never calls
// Gemini. The disclaimer arrives in its own field and is shown with every answer.
import { api } from './client';
import { ApiError, GENERIC_ERROR, toApiError } from './errors';
import type { components } from './schema';

export type Answer = components['schemas']['AnswerOut'];
export type AnswerStatus = Answer['status'];

export const AI_MESSAGES = {
  // UX State Patterns, «AI cannot answer / low confidence».
  unsure: 'Usikker på svaret her — spør gjerne på nytt eller sjekk med noen andre',
  failed: 'Vi fikk ikke svar akkurat nå. Du kan fortsatt krysse av oppgaven.',
  loading: 'Henter svar …',
  external: 'Spørsmålet sendes til en ekstern KI-tjeneste (Google Gemini).',
  demo:
    'Demo-svar: ingen KI-nøkkel er satt, så svaret er ferdigskrevet og svarer ikke på selve ' +
    'spørsmålet. Med nøkkel sendes spørsmålet til en ekstern KI-tjeneste (Google Gemini).',
  questionLabel: 'Spør KI om mer',
  ask: 'Spør',
  retry: 'Prøv igjen',
  limit: (detail: string, resetsAt: string) => `${detail} Du kan spørre igjen ${formatReset(resetsAt)}.`,
} as const;

export const QUESTION_MAX_LENGTH = 300;

const RESET_DATE = new Intl.DateTimeFormat('nb-NO', { dateStyle: 'short' });
const RESET_TIME = new Intl.DateTimeFormat('nb-NO', { hour: '2-digit', minute: '2-digit' });

/** «13.11.2026 kl. 01:00» in the viewer's time zone, from the server's timestamp. */
export function formatReset(resetsAt: string): string {
  const moment = new Date(resetsAt);
  return `${RESET_DATE.format(moment)} kl. ${RESET_TIME.format(moment)}`;
}

/** The 429: today's calls are used. `message` already says when they come back. */
export class AiLimitError extends ApiError {
  constructor(detail: string, resetsAt: string) {
    super(429, AI_MESSAGES.limit(detail, resetsAt));
    this.name = 'AiLimitError';
  }
}

/**
 * Asks the AI about a Task. A blank or missing question asks the server's default. 429 becomes
 * an AiLimitError; a 404 carries the server's reason; anything else the generic message. A
 * failed provider is not an error here: it is a 200 with status "error".
 */
export async function askTask(homeId: string, taskId: string, question?: string): Promise<Answer> {
  const { data, error, response } = await api.POST('/api/homes/{home_id}/tasks/{task_id}/answer', {
    params: { path: { home_id: homeId, task_id: taskId } },
    body: question ? { question } : {},
  });
  if (data) return data;
  if (response.status === 429 && error && 'resets_at' in error) {
    throw new AiLimitError(error.detail, error.resets_at);
  }
  throw toApiError(response, error, { passThrough: [404], fallback: GENERIC_ERROR });
}

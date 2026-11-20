// Story 5.1 (FR-14, AD-4): «?» on a Task. The server's AI service answers; React never calls
// Gemini. The disclaimer arrives in its own field and is shown with every answer.
// Story 5.2 (FR-15): the chat asks through the same call, sending the earlier turns again.
import { api } from './client';
import { ApiError, GENERIC_ERROR, toApiError } from './errors';
import type { components } from './schema';

export type Answer = components['schemas']['AnswerOut'];
export type AnswerStatus = Answer['status'];
export type ChatTurn = components['schemas']['HistoryEntry'];
/** One completed exchange of a chat: the question and the answer it got (ok or low_confidence). */
export type Exchange = { question: string; answer: Answer };

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
  askMore: 'Spør mer',
  chatEmpty: (taskName: string) => `Still et spørsmål om «${taskName}».`,
  chatLabel: (taskName: string) => `Spør KI om «${taskName}»`,
  send: 'Send',
  you: 'Du',
  assistant: 'KI',
  backToTask: (taskName: string) => `Tilbake til «${taskName}»`,
  retry: 'Prøv igjen',
  limit: (detail: string, resetsAt: string) => `${detail} Du kan spørre igjen ${formatReset(resetsAt)}.`,
} as const;

export const QUESTION_MAX_LENGTH = 300;
/** The server's limit on an earlier answer in a chat's history. */
export const HISTORY_ANSWER_MAX_LENGTH = 2000;
/**
 * The server's disclaimer text, for a chat that has no answer yet (empty chat, or a first message
 * that failed without one). Every answer brings the server's own, which replaces this; a test on
 * the backend keeps the two equal (AD-4).
 */
export const FALLBACK_DISCLAIMER =
  'KI kan ta feil. Vær forsiktig, særlig med kjemikalier og rengjøringsmidler: les og følg alltid instruksjonene på produktet.';
/** The server accepts at most this many earlier entries (five exchanges). */
export const HISTORY_MAX_ENTRIES = 10;

/** The question «?» asks when none is typed. The server builds its own default; this is only
 *  the text shown and sent as history when the chat continues from such an answer. */
export function defaultQuestion(taskName: string): string {
  return `Hvordan gjør jeg «${taskName}»?`;
}

/**
 * The earlier turns to send with the next message: the completed exchanges, flattened. The oldest
 * pairs are dropped past the server's limit, so the list keeps alternating user, assistant. An
 * answer longer than the server accepts is cut: it is context only, and a 422 would stick the chat.
 */
export function historyOf(exchanges: Exchange[]): ChatTurn[] {
  const turns = exchanges.flatMap<ChatTurn>((e) => [
    { role: 'user', text: e.question },
    { role: 'assistant', text: e.answer.answer.slice(0, HISTORY_ANSWER_MAX_LENGTH) },
  ]);
  return turns.slice(Math.max(0, turns.length - HISTORY_MAX_ENTRIES));
}

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
 * Asks the AI about a Task; `history` is a chat's earlier turns (Story 5.2), empty for «?». A blank or missing question asks the server's default. 429 becomes
 * an AiLimitError; a 404 carries the server's reason; anything else the generic message. A
 * failed provider is not an error here: it is a 200 with status "error".
 */
export async function askTask(
  homeId: string,
  taskId: string,
  question?: string,
  history: ChatTurn[] = [],
): Promise<Answer> {
  const { data, error, response } = await api.POST('/api/homes/{home_id}/tasks/{task_id}/answer', {
    params: { path: { home_id: homeId, task_id: taskId } },
    body: question ? (history.length > 0 ? { question, history } : { question }) : {},
  });
  if (data) return data;
  if (response.status === 429 && error && 'resets_at' in error) {
    throw new AiLimitError(error.detail, error.resets_at);
  }
  throw toApiError(response, error, { passThrough: [404], fallback: GENERIC_ERROR });
}

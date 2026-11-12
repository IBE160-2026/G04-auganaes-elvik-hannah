// Story 2.1 (FR-4, FR-8, AD-6): the TaskType catalog, Task Setup and a Home's Tasks.
// The recommendations come from the server's catalog (GET /api/task-types), never from here;
// this module only names the fixed intervals and the Must/Should labels.
// Story 2.2 (FR-6, decisions 1 and 8): the due text, from the server's due_status and
// days_until_due, never from the browser's clock.
// Story 2.3 (FR-5, FR-8): adjusting a Task's Må/Bør and Frequency on Task Detail.
// Story 2.4 (FR-7, FR-17, AD-3): completing a Task's open instance, and the completion note from
// the server's completion (who, how many days ago, this year or not), never the browser's clock.
import { api } from './client';
import { ApiError, GENERIC_ERROR, toApiError } from './errors';
import type { components } from './schema';

export type Task = components['schemas']['TaskOut'];
export type TaskTypes = components['schemas']['TaskTypesOut'];
export type TaskType = components['schemas']['TaskTypeOut'];
export type TaskChoice = components['schemas']['TaskChoiceIn'];
export type TaskChanges = components['schemas']['AdjustTaskRequest'];
export type Classification = Task['classification'];
export type Frequency = Task['frequency_days'];
export type DueStatus = Task['due_status'];
export type Completion = components['schemas']['CompletionOut'];

export const TASK_MESSAGES = {
  loadFailed: 'Vi fikk ikke hentet oppgavene.',
  typesLoadFailed: 'Vi fikk ikke hentet oppgaveforslagene.',
  noneChosen: 'Velg minst én oppgave.',
  setupFailed: GENERIC_ERROR,
  tenantWaiting: 'Utleier har ikke satt opp oppgaver ennå.',
  refreshed: 'Oppdatert',
  refreshFailed: 'Vi fikk ikke oppdatert oppgavene.',
  // Decision 2 and 10: shown above the full list when nothing is overdue or due soon.
  nothingDueHousehold: 'Ingen oppgaver akkurat nå — nyt det! 🎉',
  nothingDueLandlord: 'Ingen aktive oppgaver i dette hjemmet.',
  // Story 2.3 (decision 2): saved with «Lagre endringer».
  saved: 'Lagret',
  nothingToSave: 'Ingen endringer å lagre.',
  saveFailed: GENERIC_ERROR,
  // UX-DR30: the label on a Tenant's locked fields.
  lockedByLandlord: 'Satt av utleier',
  // Story 2.4: a tick the server refused (not a network error or 5xx, which are retried).
  completeFailed: (name: string) => `Vi fikk ikke krysset av «${name}». Prøv igjen.`,
} as const;

// Story 2.4 (UX-DR32): the checkbox names the action and the Task; a completed one says so.
export const checkboxLabel = (name: string) => `Merk «${name}» som fullført`;
export const completedLabel = (name: string) => `«${name}» er fullført`;

// Text first; the badge colour only reinforces it.
export const CLASSIFICATION_LABELS: Record<Classification, string> = {
  must: 'Må',
  should: 'Bør',
};

// Decision 6: the fixed intervals. A Record over the schema's union, so a new interval on the
// server fails the build until it has a label here.
export const FREQUENCY_LABELS: Record<Frequency, string> = {
  7: 'Hver uke',
  14: 'Hver 2. uke',
  30: 'Hver måned',
  42: 'Hver 6. uke',
  60: 'Hver 2. måned',
  90: 'Hver 3. måned',
  182: 'Hvert halvår',
  365: 'Hvert år',
};

// Story 2.3: the intervals a Task's Frequency can be changed to, shortest first (integer keys
// keep ascending order). From the labels, so Task Detail needs no catalog query.
export const FREQUENCIES = Object.keys(FREQUENCY_LABELS).map(Number) as Frequency[];

const DUE_FORMAT = new Intl.DateTimeFormat('nb-NO', { day: 'numeric', month: 'long' });
const DUE_FORMAT_WITH_YEAR = new Intl.DateTimeFormat('nb-NO', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
});

/**
 * «9. desember» from "2026-12-09", with the year when it is not this year. Built from the parts
 * as a local date: new Date('2026-12-09') is UTC midnight, the day before west of Greenwich.
 */
export function formatDueOn(dueOn: string, today: Date = new Date()): string {
  const year = Number(dueOn.split('-')[0]);
  return formatDate(dueOn, year !== today.getFullYear());
}

/**
 * Story 2.4 (decision 4): «Fullført i dag», «Fullført i går», «Fullført 3. november» (with the
 * year when not this year), plus « av Peter» for another current Member or « av tidligere
 * medlem». One's own completion never has a name. All from the server's fields.
 */
export function completionText(completion: Completion): string {
  const when =
    completion.days_since <= 0
      ? 'i dag'
      : completion.days_since === 1
        ? 'i går'
        : formatDate(completion.completed_on, !completion.completed_this_year);
  const by =
    completion.by === 'member' && completion.name
      ? ` av ${completion.name}`
      : completion.by === 'former_member'
        ? ' av tidligere medlem'
        : '';
  return `Fullført ${when}${by}`;
}

/** The note for a tick still on its way to the server: one's own, today. */
export const PENDING_COMPLETION_TEXT = 'Fullført i dag';

function formatDate(isoDate: string, withYear: boolean): string {
  const [year, month, day] = isoDate.split('-').map(Number);
  return (withYear ? DUE_FORMAT_WITH_YEAR : DUE_FORMAT).format(new Date(year, month - 1, day));
}

function inDays(days: number): string {
  if (days === 0) return 'i dag';
  if (days === 1) return 'i morgen';
  return `om ${days} dager`;
}

/**
 * «Forfalt — frist var 26. september», «Snart forfall — i morgen», «Neste gang: 9. desember».
 * The words follow the server's status and day count, so they always agree with the colour.
 */
export function dueText(task: Pick<Task, 'due_on' | 'due_status' | 'days_until_due'>, today?: Date): string {
  switch (task.due_status) {
    case 'overdue':
      return `Forfalt — frist var ${formatDueOn(task.due_on, today)}`;
    case 'due_soon':
      return `Snart forfall — ${inDays(task.days_until_due)}`;
    case 'later':
      return `Neste gang: ${formatDueOn(task.due_on, today)}`;
  }
}

export async function fetchTaskTypes(): Promise<TaskTypes> {
  const { data, response } = await api.GET('/api/task-types');
  if (!data) throw new ApiError(response.status, TASK_MESSAGES.typesLoadFailed);
  return data;
}

/** The Home's Tasks, Must first. Any failure gets the one load message. */
export async function fetchTasks(homeId: string): Promise<Task[]> {
  const { data, response } = await api.GET('/api/homes/{home_id}/tasks', {
    params: { path: { home_id: homeId } },
  });
  if (!data) throw new ApiError(response.status, TASK_MESSAGES.loadFailed);
  return data.tasks;
}

/**
 * Creates the chosen Tasks and returns the Home's Tasks, as GET does. A 409 or a domain 422
 * carries the server's Norwegian reason; a shape 422 (the form cannot produce one) and anything
 * else get the generic message.
 */
export async function setUpTasks(homeId: string, tasks: TaskChoice[]): Promise<Task[]> {
  const { data, error, response } = await api.POST('/api/homes/{home_id}/tasks/setup', {
    params: { path: { home_id: homeId } },
    body: { tasks },
  });
  if (!data) {
    throw toApiError(response, error, { passThrough: [409, 422], fallback: TASK_MESSAGES.setupFailed });
  }
  return data.tasks;
}

/**
 * Story 2.3: changes the Task's Må/Bør and/or Frequency; only the changed fields are sent.
 * A 404 (not in this Home) or a domain 422 carries the server's reason; anything else, including
 * a 5xx, gets the generic message. A 403 is the global handler's.
 */
export async function adjustTask(homeId: string, taskId: string, changes: TaskChanges): Promise<Task> {
  const { data, error, response } = await api.PATCH('/api/homes/{home_id}/tasks/{task_id}', {
    params: { path: { home_id: homeId, task_id: taskId } },
    body: changes,
  });
  if (!data) {
    throw toApiError(response, error, { passThrough: [404, 422], fallback: TASK_MESSAGES.saveFailed });
  }
  return data;
}

/**
 * Story 2.4: completes the Task's open instance and returns the Task as the list shows it. The
 * call is idempotent on the server, so a retry after a lost response changes nothing. A network
 * failure throws as fetch does (not an ApiError), so the caller can tell it from a refusal.
 * A 403 is the global handler's.
 */
export async function completeTask(homeId: string, task: Pick<Task, 'id' | 'instance_id' | 'name'>): Promise<Task> {
  const { data, error, response } = await api.POST(
    '/api/homes/{home_id}/tasks/{task_id}/instances/{instance_id}/completion',
    { params: { path: { home_id: homeId, task_id: task.id, instance_id: task.instance_id } } },
  );
  if (!data) {
    throw toApiError(response, error, { passThrough: [], fallback: TASK_MESSAGES.completeFailed(task.name) });
  }
  return data;
}

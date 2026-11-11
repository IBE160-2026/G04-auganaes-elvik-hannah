// Story 1.2 test helper: stubs globalThis.fetch with handlers per "METHOD /path".
// Story 1.8: Homes carry can_leave and Members can_remove, as the server sends them.
// Story 2.1: Homes carry can_set_up_tasks and has_tasks; every Home's tasks list and the
// catalog answer by default.
// Story 2.2: tasks carry due_status and days_until_due; OLAS_TASKS has one of each due state.
// Story 2.3: Homes carry can_adjust_tasks; OLAS_TENANCY is a Tenant's Home; adjustHandler
// answers PATCH /api/homes/<id>/tasks/<taskId>.
import type { Home, HomeType, Member } from '../api/homes';
import { setSession } from '../api/session';
import type { Task, TaskTypes } from '../api/tasks';

export type Handler = (request: Request) => Response | Promise<Response>;

export function json(status: number, body?: unknown): Response {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export const OLA = { id: '00000000-0000-4000-8000-000000000001', email: 'ola@example.com', name: 'Ola' };

export function authResponse(accessToken: string, user = OLA) {
  return { access_token: accessToken, token_type: 'bearer', user };
}

/** Installs the handlers; unknown routes answer 404. Returns the list of requests made. */
export function fakeApi(handlers: Record<string, Handler>) {
  const requests: Request[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: Request) => {
      const request = input.clone();
      requests.push(request);
      const handler = handlers[`${input.method} ${new URL(input.url).pathname}`];
      return handler ? handler(input) : json(404, { detail: 'Not Found' });
    }),
  );
  const calls = (method: string, path: string) =>
    requests.filter((r) => r.method === method && new URL(r.url).pathname === path);
  return { requests, calls };
}

export function resetApi() {
  vi.unstubAllGlobals();
  setSession(null);
}

// Story 1.3: Homes as GET /api/homes returns them.
export const OLAS_HOME: Home = {
  id: '00000000-0000-4000-8000-0000000000a1',
  name: 'Kollektivet',
  type: 'household',
  role: 'household_member',
  created_at: '2026-11-07T12:00:00Z',
  can_invite: true,
  can_leave: true,
  can_set_up_tasks: true,
  has_tasks: true,
  can_adjust_tasks: true,
};

// Story 2.3: a Tenant's Home, set up by the Landlord; Ola may read but not adjust its Tasks.
export const OLAS_TENANCY: Home = {
  ...OLAS_HOME,
  id: '00000000-0000-4000-8000-0000000000b1',
  name: 'Storgata 12',
  type: 'landlord',
  role: 'tenant',
  can_invite: false,
  can_set_up_tasks: false,
  can_adjust_tasks: false,
};

// Story 1.9: lived_in_home_id is the Home where the user is Household Member or Tenant, if any.
export function homesResponse(
  homes: readonly Home[] = [OLAS_HOME],
  allowed_types: HomeType[] = [],
  lived_in_home_id: string | null = null,
) {
  return { homes, allowed_types, lived_in_home_id };
}

// Story 1.5: Ola's own row, as GET /api/homes/<id>/members returns it.
export function olaAs(role: Member['role']): Member {
  return { user_id: OLA.id, name: OLA.name, role, is_you: true, can_remove: false };
}

export const membersPath = (home: Pick<Home, 'id'>) => `/api/homes/${home.id}/members`;

// Story 2.1: tasks as GET /api/homes/<id>/tasks returns them, and the catalog.
export const tasksPath = (home: Pick<Home, 'id'>) => `/api/homes/${home.id}/tasks`;
export const setupPath = (home: Pick<Home, 'id'>) => `/api/homes/${home.id}/tasks/setup`;

export const OLAS_TASKS: Task[] = [
  {
    id: '00000000-0000-4000-8000-0000000000c1',
    task_type: 'rens-sluket',
    name: 'Rens sluket',
    classification: 'must',
    frequency_days: 30,
    due_on: '2026-12-09',
    due_status: 'later',
    days_until_due: 29,
  },
  {
    id: '00000000-0000-4000-8000-0000000000c2',
    task_type: 'gulv',
    name: 'Støvsug og vask gulvene',
    classification: 'should',
    frequency_days: 14,
    due_on: '2026-11-08',
    due_status: 'overdue',
    days_until_due: -2,
  },
  {
    id: '00000000-0000-4000-8000-0000000000c3',
    task_type: 'stekeovn',
    name: 'Vask stekeovnen',
    classification: 'should',
    frequency_days: 90,
    due_on: '2026-11-11',
    due_status: 'due_soon',
    days_until_due: 1,
  },
];

export const taskPath = (home: Pick<Home, 'id'>, task: Pick<Task, 'id'>) => `${tasksPath(home)}/${task.id}`;

/**
 * Story 2.3: a PATCH handler. 200 answers the Task with the sent fields applied (and records the
 * body in `bodies`); 403, 404 and 500 answer as the server would.
 */
export function adjustHandler(
  task: Task,
  status: 200 | 403 | 404 | 500 = 200,
  bodies: unknown[] = [],
): Handler {
  return async (request) => {
    const body = (await request.json()) as Partial<Task>;
    bodies.push(body);
    if (status === 403) return json(403, { detail: 'Du har ikke tilgang til dette hjemmet.' });
    if (status === 404) return json(404, { detail: 'Fant ikke oppgaven.' });
    if (status === 500) return json(500, { detail: 'Internal Server Error' });
    return json(200, { ...task, ...body });
  };
}

export const TASK_TYPES: TaskTypes = {
  catalog_version: 1,
  task_types: [
    { key: 'vask-badet', name: 'Vask badet grundig', classification: 'must', frequency_days: 42, photo_evidence_eligible: false },
    { key: 'rens-sluket', name: 'Rens sluket', classification: 'must', frequency_days: 30, photo_evidence_eligible: true },
    { key: 'stekeovn', name: 'Vask stekeovnen', classification: 'should', frequency_days: 90, photo_evidence_eligible: false },
  ],
  frequencies: [7, 14, 30, 42, 60, 90, 182, 365],
};

/**
 * Signed in as Ola on load, with these Homes; each Home's members list holds only Ola, each
 * Home's tasks are OLAS_TASKS (none when it has no Tasks), and the catalog is TASK_TYPES.
 */
export function signedInWith(
  homes: readonly Home[] = [OLAS_HOME],
  allowed_types: HomeType[] = [],
  lived_in_home_id: string | null = null,
): Record<string, Handler> {
  return {
    'POST /api/auth/refresh': () => json(200, authResponse('a1')),
    'GET /api/auth/me': () => json(200, OLA),
    'GET /api/homes': () => json(200, homesResponse(homes, allowed_types, lived_in_home_id)),
    'GET /api/task-types': () => json(200, TASK_TYPES),
    ...Object.fromEntries(
      homes.flatMap((home) => [
        [`GET ${membersPath(home)}`, () => json(200, { members: [olaAs(home.role)] })],
        [`GET ${tasksPath(home)}`, () => json(200, { tasks: home.has_tasks ? OLAS_TASKS : [] })],
      ]),
    ),
  };
}

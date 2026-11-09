// Story 1.2 test helper: stubs globalThis.fetch with handlers per "METHOD /path".
// Story 1.8: Homes carry can_leave and Members can_remove, as the server sends them.
// Story 2.1: Homes carry can_set_up_tasks and has_tasks; every Home's tasks list and the
// catalog answer by default.
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
};

export function homesResponse(homes: readonly Home[] = [OLAS_HOME], allowed_types: HomeType[] = []) {
  return { homes, allowed_types };
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
  },
  {
    id: '00000000-0000-4000-8000-0000000000c2',
    task_type: 'gulv',
    name: 'Støvsug og vask gulvene',
    classification: 'should',
    frequency_days: 14,
    due_on: '2026-11-23',
  },
];

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
): Record<string, Handler> {
  return {
    'POST /api/auth/refresh': () => json(200, authResponse('a1')),
    'GET /api/auth/me': () => json(200, OLA),
    'GET /api/homes': () => json(200, homesResponse(homes, allowed_types)),
    'GET /api/task-types': () => json(200, TASK_TYPES),
    ...Object.fromEntries(
      homes.flatMap((home) => [
        [`GET ${membersPath(home)}`, () => json(200, { members: [olaAs(home.role)] })],
        [`GET ${tasksPath(home)}`, () => json(200, { tasks: home.has_tasks ? OLAS_TASKS : [] })],
      ]),
    ),
  };
}

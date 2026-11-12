// Story 2.1 (FR-4, FR-8, AD-6): Task Setup, one test per frontend row of the spec's matrix.
// Story 2.2 (decision 12): success, a 409 and the guard go to this Home's /hjem/<id>, never "/".
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import type { Home } from '../api/homes';
import { lastHomeKey } from '../api/lastHome';
import { TASK_MESSAGES, type Task } from '../api/tasks';
import {
  OLA,
  OLAS_HOME,
  TASK_TYPES,
  fakeApi,
  homesResponse,
  json,
  resetApi,
  setupPath,
  signedInWith,
  tasksPath,
} from '../test-utils/fakeApi';

const NEW_HOME: Home = { ...OLAS_HOME, has_tasks: false };
const PAGE = `/hjem/${NEW_HOME.id}/oppgaveoppsett`;
const OVERVIEW = `/hjem/${NEW_HOME.id}`;
const OTHER: Home = { ...OLAS_HOME, id: '00000000-0000-4000-8000-0000000000b1', name: 'Storgata 12', type: 'landlord', role: 'landlord' };
const ALREADY_SET_UP = 'Oppgavene i dette hjemmet er allerede satt opp.';

// What POST …/tasks/setup answers after the test's choices below.
const CREATED: Task[] = [
  {
    id: '00000000-0000-4000-8000-0000000000d1',
    instance_id: '00000000-0000-4000-8000-0000000000e1',
    task_type: 'vask-badet',
    name: 'Vask badet grundig',
    classification: 'must',
    frequency_days: 42,
    due_on: '2026-12-21',
    due_status: 'later',
    days_until_due: 42,
    completion: null,
  },
  {
    id: '00000000-0000-4000-8000-0000000000d2',
    instance_id: '00000000-0000-4000-8000-0000000000e2',
    task_type: 'stekeovn',
    name: 'Vask stekeovnen',
    classification: 'must',
    frequency_days: 60,
    due_on: '2027-01-08',
    due_status: 'later',
    days_until_due: 60,
    completion: null,
  },
];

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

function row(name: string) {
  return screen.getByRole('group', { name });
}

function save() {
  return userEvent.click(screen.getByRole('button', { name: 'Lagre oppgavene' }));
}

afterEach(resetApi);

describe('Task Setup', () => {
  it('shows one row per catalog entry with the recommended values', async () => {
    fakeApi(signedInWith([NEW_HOME]));
    renderAt(PAGE);

    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
    const groups = await screen.findAllByRole('group');
    expect(groups.map((g) => g.querySelector('legend')?.textContent)).toEqual(TASK_TYPES.task_types.map((t) => t.name));

    const bad = row('Vask badet grundig');
    expect(within(bad).getByRole('checkbox', { name: 'Ta med' })).toBeChecked();
    expect(within(bad).getByRole('radio', { name: 'Må' })).toBeChecked();
    expect(within(bad).getByRole('combobox', { name: 'Hvor ofte' })).toHaveValue('42');
    expect(within(row('Vask stekeovnen')).getByRole('radio', { name: 'Bør' })).toBeChecked();
    expect(within(row('Vask stekeovnen')).getByRole('combobox')).toHaveDisplayValue('Hver 3. måned');
  });

  it('gives each row its own radio group', async () => {
    fakeApi(signedInWith([NEW_HOME]));
    renderAt(PAGE);

    await screen.findAllByRole('group');
    const names = screen.getAllByRole('radio').map((r) => r.getAttribute('name'));
    expect(new Set(names).size).toBe(TASK_TYPES.task_types.length);
  });

  it('saves one adjusted and one unticked task, lands on this Home and lists them without bouncing back', async () => {
    let saved = false;
    // Another Home was used last: success still goes to this one, not to what "/" would pick.
    localStorage.setItem(lastHomeKey(OLA.id), OTHER.id);
    const server = fakeApi({
      ...signedInWith([OTHER, NEW_HOME], ['landlord']),
      // After the save neither refetch answers: only the cache writes can show the list.
      'GET /api/homes': () =>
        saved ? new Promise<Response>(() => {}) : json(200, homesResponse([OTHER, NEW_HOME], ['landlord'])),
      [`GET ${tasksPath(NEW_HOME)}`]: () => new Promise<Response>(() => {}),
      [`POST ${setupPath(NEW_HOME)}`]: () => {
        saved = true;
        return json(201, { tasks: CREATED });
      },
    });
    renderAt(PAGE);

    await screen.findAllByRole('group');
    await userEvent.click(within(row('Rens sluket')).getByRole('checkbox', { name: 'Ta med' }));
    const ovn = row('Vask stekeovnen');
    await userEvent.click(within(ovn).getByRole('radio', { name: 'Må' }));
    await userEvent.selectOptions(within(ovn).getByRole('combobox'), 'Hver 2. måned');
    const entries = window.history.length;
    await save();

    const section = await screen.findByRole('region', { name: 'Oppgaver' });
    expect(within(section).getByText('Vask stekeovnen')).toBeInTheDocument();
    expect(within(section).queryByText('Rens sluket')).not.toBeInTheDocument();
    expect(window.location.pathname).toBe(OVERVIEW);
    // replace: Back does not return to the setup form.
    expect(window.history.length).toBe(entries);

    const [request] = server.calls('POST', setupPath(NEW_HOME));
    expect(await request.json()).toEqual({
      tasks: [
        { task_type: 'vask-badet', classification: 'must', frequency_days: 42 },
        { task_type: 'stekeovn', classification: 'must', frequency_days: 60 },
      ],
    });
  });

  it('keeps an unticked row\'s controls enabled', async () => {
    fakeApi(signedInWith([NEW_HOME]));
    renderAt(PAGE);

    await screen.findAllByRole('group');
    const sluk = row('Rens sluket');
    await userEvent.click(within(sluk).getByRole('checkbox', { name: 'Ta med' }));

    expect(within(sluk).getByRole('checkbox')).not.toBeChecked();
    for (const control of [...within(sluk).getAllByRole('radio'), within(sluk).getByRole('combobox')]) {
      expect(control).toBeEnabled();
    }
  });

  it('asks for at least one task before sending, with focus on the first checkbox', async () => {
    const server = fakeApi(signedInWith([NEW_HOME]));
    renderAt(PAGE);

    await screen.findAllByRole('group');
    for (const box of screen.getAllByRole('checkbox', { name: 'Ta med' })) await userEvent.click(box);
    await save();

    expect(await screen.findByRole('alert')).toHaveTextContent(TASK_MESSAGES.noneChosen);
    const [first] = screen.getAllByRole('checkbox', { name: 'Ta med' });
    await waitFor(() => expect(first).toHaveFocus());
    expect(first).toHaveAccessibleDescription(TASK_MESSAGES.noneChosen);
    expect(server.calls('POST', setupPath(NEW_HOME))).toHaveLength(0);
  });

  it('after a 409, waits for the server and goes to this Home without a bounce', async () => {
    let conflicted = false;
    const server = fakeApi({
      ...signedInWith([NEW_HOME]),
      // Set up in another tab: the server now says the Home has Tasks.
      'GET /api/homes': () => json(200, homesResponse([conflicted ? OLAS_HOME : NEW_HOME])),
      [`POST ${setupPath(NEW_HOME)}`]: () => {
        conflicted = true;
        return json(409, { detail: ALREADY_SET_UP });
      },
    });
    renderAt(PAGE);

    await screen.findAllByRole('group');
    await save();

    expect(await screen.findByRole('region', { name: 'Oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(OVERVIEW);
    // The form, and its message, are gone with the redirect.
    expect(screen.queryByText(ALREADY_SET_UP)).not.toBeInTheDocument();
    expect(server.calls('POST', setupPath(NEW_HOME))).toHaveLength(1);
  });

  it('after a 409 whose Homes refetch fails, shows the server\'s reason and stays', async () => {
    let conflicted = false;
    fakeApi({
      ...signedInWith([NEW_HOME]),
      'GET /api/homes': () => (conflicted ? json(500, { detail: 'x' }) : json(200, homesResponse([NEW_HOME]))),
      [`POST ${setupPath(NEW_HOME)}`]: () => {
        conflicted = true;
        return json(409, { detail: ALREADY_SET_UP });
      },
    });
    renderAt(PAGE);

    await screen.findAllByRole('group');
    await save();

    expect(await screen.findByRole('alert')).toHaveTextContent(ALREADY_SET_UP);
    expect(window.location.pathname).toBe(PAGE);
  });

  it('after a 403, shows no inline error and the refetch sends the user away', async () => {
    let removed = false;
    fakeApi({
      ...signedInWith([NEW_HOME]),
      'GET /api/homes': () => json(200, removed ? homesResponse([], ['household', 'landlord']) : homesResponse([NEW_HOME])),
      [`POST ${setupPath(NEW_HOME)}`]: () => {
        removed = true;
        return json(403, { detail: 'Du har ikke tilgang til dette i dette hjemmet.' });
      },
    });
    renderAt(PAGE);

    await screen.findAllByRole('group');
    await save();

    expect(await screen.findByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
    expect(screen.queryByText(/ikke tilgang/)).not.toBeInTheDocument();
  });

  it('shows a failed save inline with «Prøv igjen» and stays on the page', async () => {
    let fail = true;
    let saved = false;
    fakeApi({
      ...signedInWith([NEW_HOME]),
      'GET /api/homes': () => json(200, homesResponse([saved ? OLAS_HOME : NEW_HOME])),
      [`POST ${setupPath(NEW_HOME)}`]: () => {
        if (fail) return json(500, { detail: 'x' });
        saved = true;
        return json(201, { tasks: CREATED });
      },
    });
    renderAt(PAGE);

    await screen.findAllByRole('group');
    await save();

    expect(await screen.findByRole('alert')).toHaveTextContent(TASK_MESSAGES.setupFailed);
    expect(window.location.pathname).toBe(PAGE);
    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));
    expect(await screen.findByRole('region', { name: 'Oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(OVERVIEW);
  });

  it('shows a network failure inline too', async () => {
    fakeApi({
      ...signedInWith([NEW_HOME]),
      [`POST ${setupPath(NEW_HOME)}`]: () => Promise.reject(new TypeError('Failed to fetch')),
    });
    renderAt(PAGE);

    await screen.findAllByRole('group');
    await save();

    expect(await screen.findByRole('alert')).toHaveTextContent(TASK_MESSAGES.setupFailed);
    expect(window.location.pathname).toBe(PAGE);
  });

  it('shows a failed catalog load with a retry', async () => {
    let fail = true;
    fakeApi({
      ...signedInWith([NEW_HOME]),
      'GET /api/task-types': () => (fail ? json(500, { detail: 'x' }) : json(200, TASK_TYPES)),
    });
    renderAt(PAGE);

    expect(await screen.findByRole('alert')).toHaveTextContent(TASK_MESSAGES.typesLoadFailed);
    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));
    expect(await screen.findAllByRole('group')).toHaveLength(TASK_TYPES.task_types.length);
  });

  it.each([
    ['a Tenant', { ...NEW_HOME, role: 'tenant', can_invite: false, can_set_up_tasks: false, can_adjust_tasks: false } as Home],
    ['a Home already set up', OLAS_HOME],
  ])('sends %s to its Task Overview', async (_case, home) => {
    const server = fakeApi(signedInWith([home]));
    renderAt(PAGE);

    expect(await screen.findByRole('heading', { level: 1, name: home.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(OVERVIEW);
    expect(server.calls('GET', '/api/task-types')).toHaveLength(0);
  });

  it('sends a Home that is not among the user\'s to "/" (then the user\'s Home) without fetching anything for it', async () => {
    const server = fakeApi(signedInWith([OLAS_HOME]));
    const foreign = '00000000-0000-4000-8000-0000000000ff';
    renderAt(`/hjem/${foreign}/oppgaveoppsett`);

    expect(await screen.findByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}`);
    expect(server.requests.some((r) => r.url.includes(foreign))).toBe(false);
  });

  it('waits while the Homes are loading', async () => {
    const server = fakeApi({ ...signedInWith([NEW_HOME]), 'GET /api/homes': () => new Promise<Response>(() => {}) });
    renderAt(PAGE);

    await waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(1));
    expect(screen.getByRole('status')).toHaveTextContent('Laster …');
    expect(window.location.pathname).toBe(PAGE);
  });

  it('links to «Medlemmer og invitasjon» for this Home', async () => {
    fakeApi(signedInWith([NEW_HOME]));
    renderAt(PAGE);

    await userEvent.click(await screen.findByRole('link', { name: 'Medlemmer og invitasjon' }));

    expect(await screen.findByRole('heading', { name: 'Medlemmer og invitasjon' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${NEW_HOME.id}/medlemmer`);
  });

  it('signs out from the setup page', async () => {
    const server = fakeApi({
      ...signedInWith([NEW_HOME]),
      'POST /api/auth/logout': () => new Response(null, { status: 204 }),
    });
    renderAt(PAGE);

    await userEvent.click(await screen.findByRole('button', { name: 'Logg ut' }));

    expect(await screen.findByRole('heading', { name: 'Logg inn' })).toBeInTheDocument();
    expect(server.calls('POST', '/api/auth/logout')).toHaveLength(1);
  });
});

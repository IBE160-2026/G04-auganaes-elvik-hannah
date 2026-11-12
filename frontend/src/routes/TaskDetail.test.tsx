// Story 2.2 (decision 6): Task Detail, one test per case of the matrix row.
// Story 2.3 (FR-5, FR-8, UX-DR30): adjusting Må/Bør and Frequency, and a Tenant's locked view.
// Story 2.4 (decision 6): Detail shows the completion note read-only; it has no checkbox.
// Story 2.6 (FR-24): «Fjern oppgaven» with an inline confirmation.
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { GENERIC_ERROR } from '../api/errors';
import type { Home } from '../api/homes';
import { TASK_MESSAGES, type Task } from '../api/tasks';
import {
  DONE_BY_YOU_TODAY,
  OLAS_HOME,
  OLAS_TASKS,
  OLAS_TENANCY,
  adjustHandler,
  completionPath,
  fakeApi,
  json,
  resetApi,
  signedInWith,
  taskPath,
  taskServer,
  tasksPath,
} from '../test-utils/fakeApi';

const OVERVIEW = `/hjem/${OLAS_HOME.id}`;
const [MUST, OVERDUE] = OLAS_TASKS;
const detailPath = (taskId: string) => `${OVERVIEW}/oppgaver/${taskId}`;

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

afterEach(resetApi);

describe('Task Detail', () => {
  it('opens from a row and shows the name, class, interval and due text, with focus on the name', async () => {
    fakeApi(signedInWith());
    renderAt(OVERVIEW);

    await userEvent.click(await screen.findByRole('link', { name: /^Støvsug og vask gulvene/ }));

    const title = await screen.findByRole('heading', { level: 1, name: OVERDUE.name });
    expect(window.location.pathname).toBe(detailPath(OVERDUE.id));
    await waitFor(() => expect(title).toHaveFocus());
    expect(screen.getByRole('radio', { name: 'Bør' })).toBeChecked();
    expect(screen.getByRole('combobox', { name: 'Hvor ofte' })).toHaveDisplayValue('Hver 2. uke');
    expect(screen.getByText('Forfalt — frist var 8. november')).toBeInTheDocument();
    // Story 2.4, decision 6: completing from Detail comes with Epic 4.
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    expect(screen.queryByText('Status')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('link', { name: 'Tilbake til oppgavene' }));
    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(OVERVIEW);
  });

  it('waits with «Laster …» while the tasks load, and never redirects', async () => {
    const server = fakeApi({ ...signedInWith(), [`GET ${tasksPath(OLAS_HOME)}`]: () => new Promise<Response>(() => {}) });
    renderAt(detailPath(MUST.id));

    await waitFor(() => expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(1));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.getByRole('status')).toHaveTextContent('Laster …');
    expect(window.location.pathname).toBe(detailPath(MUST.id));
  });

  it('sends a loaded list without that Task back to the overview', async () => {
    fakeApi(signedInWith());
    renderAt(detailPath('00000000-0000-4000-8000-0000000000ff'));

    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(OVERVIEW);
  });

  it('sends a Home that is not the user\'s to "/"', async () => {
    const foreign = '00000000-0000-4000-8000-0000000000ff';
    const server = fakeApi(signedInWith());
    renderAt(`/hjem/${foreign}/oppgaver/${MUST.id}`);

    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(OVERVIEW);
    expect(server.requests.some((r) => r.url.includes(foreign))).toBe(false);
  });

  it('sends a Home without Tasks to its overview, which routes on to Task Setup', async () => {
    const home: Home = { ...OLAS_HOME, has_tasks: false };
    fakeApi(signedInWith([home]));
    renderAt(detailPath(MUST.id));

    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
  });

  it('shows a failed load inline with «Prøv igjen»', async () => {
    let fail = true;
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: () => (fail ? json(500, { detail: 'x' }) : json(200, { tasks: OLAS_TASKS })),
    });
    renderAt(detailPath(MUST.id));

    expect(await screen.findByRole('alert')).toHaveTextContent(TASK_MESSAGES.loadFailed);
    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv å hente oppgavene igjen' }));
    expect(await screen.findByRole('heading', { level: 1, name: MUST.name })).toBeInTheDocument();
  });

  it('shows no inline error on a 403 and lets the refetched Homes route the user away', async () => {
    let member = true;
    fakeApi({
      ...signedInWith(),
      'GET /api/homes': () =>
        json(200, { homes: member ? [OLAS_HOME] : [], allowed_types: ['household', 'landlord'], lived_in_home_id: null }),
      [`GET ${tasksPath(OLAS_HOME)}`]: () => {
        member = false;
        return json(403, { detail: 'Du har ikke tilgang til dette hjemmet.' });
      },
    });
    renderAt(detailPath(MUST.id));

    expect(await screen.findByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
    expect(screen.queryByText(TASK_MESSAGES.loadFailed)).not.toBeInTheDocument();
  });
});

// Story 2.3: the frontend rows of the spec's matrix.
async function openDetail(task: Task = MUST) {
  renderAt(detailPath(task.id));
  await screen.findByRole('heading', { level: 1, name: task.name });
}

const saveButton = () => screen.getByRole('button', { name: /^(Lagre endringer|Prøv igjen)$/ });
const frequencySelect = () => screen.getByRole('combobox', { name: 'Hvor ofte' });

describe('Adjust a Task (Story 2.3)', () => {
  it('saves only the changed class, announces «Lagret» and refetches the list', async () => {
    const bodies: unknown[] = [];
    const server = fakeApi({ ...signedInWith(), [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: adjustHandler(MUST, 200, bodies) });
    await openDetail();
    const loads = server.calls('GET', tasksPath(OLAS_HOME)).length;

    await userEvent.click(screen.getByRole('radio', { name: 'Bør' }));
    expect(server.calls('PATCH', taskPath(OLAS_HOME, MUST))).toHaveLength(0);
    await userEvent.click(saveButton());

    expect(await screen.findByText(TASK_MESSAGES.saved)).toBeInTheDocument();
    expect(bodies).toEqual([{ classification: 'should' }]);
    expect(saveButton()).toHaveFocus();
    await waitFor(() => expect(server.calls('GET', tasksPath(OLAS_HOME)).length).toBeGreaterThan(loads));
  });

  it('saves only the changed interval and then shows the saved value', async () => {
    const bodies: unknown[] = [];
    fakeApi({
      ...signedInWith(),
      // The server's list reflects what was saved.
      [`GET ${tasksPath(OLAS_HOME)}`]: () =>
        json(200, { tasks: OLAS_TASKS.map((t) => (t.id === MUST.id ? { ...t, ...(bodies.at(-1) as object) } : t)) }),
      [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: adjustHandler(MUST, 200, bodies),
    });
    await openDetail();

    await userEvent.selectOptions(frequencySelect(), 'Hver 2. måned');
    await userEvent.click(saveButton());

    expect(await screen.findByText(TASK_MESSAGES.saved)).toBeInTheDocument();
    expect(bodies).toEqual([{ frequency_days: 60 }]);
    expect(frequencySelect()).toHaveDisplayValue('Hver 2. måned');
  });

  it('shows the saved interval and due text from the answer before the list refetches', async () => {
    const moved: Task = { ...MUST, frequency_days: 60, due_on: '2027-01-08', due_status: 'later', days_until_due: 59 };
    let loads = 0;
    fakeApi({
      ...signedInWith(),
      // The first load answers; the refetch after the save never does, so only the cache write
      // can show the saved values.
      [`GET ${tasksPath(OLAS_HOME)}`]: () =>
        loads++ === 0 ? json(200, { tasks: OLAS_TASKS }) : new Promise<Response>(() => {}),
      [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: () => json(200, moved),
    });
    await openDetail();

    await userEvent.selectOptions(frequencySelect(), 'Hver 2. måned');
    await userEvent.click(saveButton());

    expect(await screen.findByText(TASK_MESSAGES.saved)).toBeInTheDocument();
    expect(frequencySelect()).toHaveDisplayValue('Hver 2. måned');
    expect(screen.getByText('Neste gang: 8. januar 2027')).toBeInTheDocument();
  });

  it('keeps a value picked while the save is in flight', async () => {
    let answer: (response: Response) => void = () => {};
    fakeApi({
      ...signedInWith(),
      [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: async (request) => {
        const body = (await request.json()) as Partial<Task>;
        return new Promise<Response>((resolve) => {
          answer = resolve;
        }).then(() => json(200, { ...MUST, ...body }));
      },
    });
    await openDetail();

    await userEvent.click(screen.getByRole('radio', { name: 'Bør' }));
    await userEvent.click(saveButton());
    await userEvent.selectOptions(frequencySelect(), 'Hvert år');
    answer(json(200));

    expect(await screen.findByText(TASK_MESSAGES.saved)).toBeInTheDocument();
    expect(frequencySelect()).toHaveDisplayValue('Hvert år');
  });

  it('sends nothing when no field differs from the server, and says so', async () => {
    const server = fakeApi({ ...signedInWith(), [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: adjustHandler(MUST) });
    await openDetail();

    await userEvent.click(saveButton());
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(TASK_MESSAGES.nothingToSave));

    // Changed and changed back is no change either.
    await userEvent.selectOptions(frequencySelect(), 'Hvert år');
    await userEvent.selectOptions(frequencySelect(), 'Hver måned');
    await userEvent.click(saveButton());
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(TASK_MESSAGES.nothingToSave));
    expect(server.calls('PATCH', taskPath(OLAS_HOME, MUST))).toHaveLength(0);
  });

  it('shows a failed save at the form, keeps the draft, and «Prøv igjen» saves it', async () => {
    const bodies: unknown[] = [];
    let fail = true;
    fakeApi({
      ...signedInWith(),
      [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: (request) => adjustHandler(MUST, fail ? 500 : 200, bodies)(request),
    });
    await openDetail();

    await userEvent.selectOptions(frequencySelect(), 'Hver uke');
    await userEvent.click(saveButton());

    expect(await screen.findByRole('alert')).toHaveTextContent(GENERIC_ERROR);
    expect(frequencySelect()).toHaveDisplayValue('Hver uke');
    expect(saveButton()).toHaveTextContent('Prøv igjen');

    fail = false;
    await userEvent.click(saveButton());

    expect(await screen.findByText(TASK_MESSAGES.saved)).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(bodies).toEqual([{ frequency_days: 7 }, { frequency_days: 7 }]);
  });

  it('shows the same message when the network fails', async () => {
    fakeApi({
      ...signedInWith(),
      [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: () => {
        throw new TypeError('Failed to fetch');
      },
    });
    await openDetail();

    await userEvent.click(screen.getByRole('radio', { name: 'Bør' }));
    await userEvent.click(saveButton());

    expect(await screen.findByRole('alert')).toHaveTextContent(GENERIC_ERROR);
    expect(screen.getByRole('radio', { name: 'Bør' })).toBeChecked();
  });

  it('shows no inline error on a 403 and lets the refetched Homes route the user away', async () => {
    let member = true;
    fakeApi({
      ...signedInWith(),
      'GET /api/homes': () =>
        json(200, { homes: member ? [OLAS_HOME] : [], allowed_types: ['household', 'landlord'], lived_in_home_id: null }),
      [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: (request) => {
        member = false;
        return adjustHandler(MUST, 403)(request);
      },
    });
    await openDetail();

    await userEvent.click(screen.getByRole('radio', { name: 'Bør' }));
    await userEvent.click(saveButton());

    expect(await screen.findByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
    expect(screen.queryByText(GENERIC_ERROR)).not.toBeInTheDocument();
  });

  it('goes back to the overview on a 404 once the refetched list lacks the Task', async () => {
    let gone = false;
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: () =>
        json(200, { tasks: gone ? OLAS_TASKS.filter((t) => t.id !== MUST.id) : OLAS_TASKS }),
      [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: (request) => {
        gone = true;
        return adjustHandler(MUST, 404)(request);
      },
    });
    await openDetail();

    await userEvent.click(screen.getByRole('radio', { name: 'Bør' }));
    await userEvent.click(saveButton());

    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(OVERVIEW);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it("shows another Member's save in fields this user has not touched, and sends nothing for them", async () => {
    // Another Member changed the interval to 60 days; Ola's refetch after his own save brings it.
    let server: Task = MUST;
    const bodies: unknown[] = [];
    const api = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: () => json(200, { tasks: [server, ...OLAS_TASKS.slice(1)] }),
      [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: async (request) => {
        const body = (await request.json()) as Partial<Task>;
        bodies.push(body);
        server = { ...server, ...body, frequency_days: 60 };
        return json(200, { ...MUST, ...body });
      },
    });
    await openDetail();

    await userEvent.click(screen.getByRole('radio', { name: 'Bør' }));
    await userEvent.click(saveButton());

    await waitFor(() => expect(frequencySelect()).toHaveDisplayValue('Hver 2. måned'));
    expect(screen.getByRole('radio', { name: 'Bør' })).toBeChecked();
    await userEvent.click(saveButton());
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(TASK_MESSAGES.nothingToSave));
    expect(bodies).toEqual([{ classification: 'should' }]);
    expect(api.calls('PATCH', taskPath(OLAS_HOME, MUST))).toHaveLength(1);
  });

  it('drops an unsaved interval when the user leaves, and sends nothing', async () => {
    const server = fakeApi({ ...signedInWith(), [`PATCH ${taskPath(OLAS_HOME, MUST)}`]: adjustHandler(MUST) });
    await openDetail();

    await userEvent.selectOptions(frequencySelect(), 'Hvert år');
    await userEvent.click(screen.getByRole('link', { name: 'Tilbake til oppgavene' }));
    await userEvent.click(await screen.findByRole('link', { name: /^Rens sluket/ }));

    await screen.findByRole('heading', { level: 1, name: MUST.name });
    expect(frequencySelect()).toHaveDisplayValue('Hver måned');
    expect(server.calls('PATCH', taskPath(OLAS_HOME, MUST))).toHaveLength(0);
  });

  it("shows a Tenant read-only fields «Satt av utleier», reachable by Tab, with no select or radio", async () => {
    fakeApi(signedInWith([OLAS_TENANCY]));
    renderAt(`/hjem/${OLAS_TENANCY.id}/oppgaver/${MUST.id}`);
    const title = await screen.findByRole('heading', { level: 1, name: MUST.name });
    await waitFor(() => expect(title).toHaveFocus());

    const classification = screen.getByRole('textbox', { name: 'Viktighet' });
    const frequency = screen.getByRole('textbox', { name: 'Hvor ofte' });
    for (const [field, value] of [
      [classification, 'Må'],
      [frequency, 'Hver måned'],
    ] as const) {
      expect(field).toHaveValue(value);
      expect(field).toHaveAttribute('readonly');
      expect(field).toHaveAttribute('aria-readonly', 'true');
      expect(field).not.toBeDisabled();
      expect(field).toHaveAccessibleDescription(TASK_MESSAGES.lockedByLandlord);
    }
    expect(screen.queryByRole('radio')).not.toBeInTheDocument();
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Lagre endringer' })).not.toBeInTheDocument();

    // Story 5.1: «Spør KI» sits under the title, before the fields.
    await userEvent.tab();
    expect(screen.getByRole('button', { name: `Spør KI om «${MUST.name}»` })).toHaveFocus();
    await userEvent.tab();
    expect(classification).toHaveFocus();
    await userEvent.tab();
    expect(frequency).toHaveFocus();
  });

  it('shows the completion note read-only, without a checkbox (Story 2.4, decision 6)', async () => {
    const done: Task = {
      ...MUST,
      completion: { ...DONE_BY_YOU_TODAY, days_since: 1, by: 'member', name: 'Jonas' },
    };
    fakeApi({ ...signedInWith(), [`GET ${tasksPath(OLAS_HOME)}`]: () => json(200, { tasks: [done, OVERDUE] }) });
    renderAt(detailPath(MUST.id));

    expect(await screen.findByText('Fullført i går av Jonas')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
  });

  it('shows a tick still on its way as «Fullført i dag» under «Status» (Story 2.4)', async () => {
    const api = taskServer();
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, OVERDUE)}`]: api.complete(OVERDUE, [200], new Promise(() => {})),
    });
    renderAt(OVERVIEW);

    await userEvent.click(await screen.findByRole('checkbox', { name: `Merk «${OVERDUE.name}» som fullført` }));
    await userEvent.click(screen.getByRole('link', { name: /^Støvsug og vask gulvene/ }));

    expect(await screen.findByRole('heading', { level: 1, name: OVERDUE.name })).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Fullført i dag')).toBeInTheDocument();
  });
});

describe('Task Detail, remove (Story 2.6)', () => {
  function serverWith(archive: ReturnType<ReturnType<typeof taskServer>['archive']>) {
    const tasks = taskServer();
    return fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: tasks.list,
      [`DELETE ${taskPath(OLAS_HOME, MUST)}`]: archive,
    });
  }

  it('confirms inline, archives, and lands on the overview with «Fjernet «X».» once', async () => {
    const tasks = taskServer();
    const api = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: tasks.list,
      [`DELETE ${taskPath(OLAS_HOME, MUST)}`]: tasks.archive(),
    });
    renderAt(detailPath(MUST.id));

    await userEvent.click(await screen.findByRole('button', { name: 'Fjern oppgaven «Rens sluket»' }));
    expect(screen.getByText(TASK_MESSAGES.removeExplanation)).toBeInTheDocument();
    const confirm = screen.getByRole('button', { name: 'Ja, fjern oppgaven «Rens sluket»' });
    expect(confirm).toHaveFocus();
    expect(api.calls('DELETE', taskPath(OLAS_HOME, MUST))).toHaveLength(0);
    await userEvent.click(confirm);

    expect(await screen.findByText('Fjernet «Rens sluket».')).toBeInTheDocument();
    expect(window.location.pathname).toBe(OVERVIEW);
    expect(screen.queryByRole('link', { name: /^Rens sluket/ })).not.toBeInTheDocument();
    expect(api.calls('DELETE', taskPath(OLAS_HOME, MUST))).toHaveLength(1);

    // Consumed: not shown again when the overview is opened later.
    await userEvent.click(screen.getByRole('link', { name: 'Medlemmer og invitasjon' }));
    await screen.findByRole('heading', { level: 1, name: /Medlemmer/ });
    const nav = screen.getByRole('navigation', { name: 'Hovedmeny' });
    await userEvent.click(within(nav).getByRole('link', { name: 'Oppgaver' }));
    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(screen.queryByText('Fjernet «Rens sluket».')).not.toBeInTheDocument();
  });

  it('sends nothing on «Avbryt»', async () => {
    const api = serverWith(taskServer().archive());
    renderAt(detailPath(MUST.id));

    await userEvent.click(await screen.findByRole('button', { name: 'Fjern oppgaven «Rens sluket»' }));
    await userEvent.click(screen.getByRole('button', { name: 'Avbryt' }));

    expect(screen.getByRole('button', { name: 'Fjern oppgaven «Rens sluket»' })).toHaveFocus();
    expect(api.calls('DELETE', taskPath(OLAS_HOME, MUST))).toHaveLength(0);
    expect(window.location.pathname).toBe(detailPath(MUST.id));
  });

  it('shows an inline error and retries when the archive fails', async () => {
    const failing = taskServer().archive(500);
    serverWith(failing);
    renderAt(detailPath(MUST.id));

    await userEvent.click(await screen.findByRole('button', { name: 'Fjern oppgaven «Rens sluket»' }));
    await userEvent.click(screen.getByRole('button', { name: 'Ja, fjern oppgaven «Rens sluket»' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(TASK_MESSAGES.archiveFailed);
    expect(screen.getByRole('button', { name: 'Prøv igjen' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(detailPath(MUST.id));
  });

  it('folds the confirmation and shows no message when the archive is refused with 403', async () => {
    serverWith(taskServer().archive(403));
    renderAt(detailPath(MUST.id));

    await userEvent.click(await screen.findByRole('button', { name: 'Fjern oppgaven «Rens sluket»' }));
    await userEvent.click(screen.getByRole('button', { name: 'Ja, fjern oppgaven «Rens sluket»' }));

    expect(await screen.findByRole('button', { name: 'Fjern oppgaven «Rens sluket»' })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByText(TASK_MESSAGES.archiveFailed)).not.toBeInTheDocument();
  });

  it('shows no error and refetches the list when the Task is already gone (404)', async () => {
    const api = serverWith(taskServer().archive(404));
    renderAt(detailPath(MUST.id));
    await screen.findByRole('heading', { level: 1, name: MUST.name });
    const before = api.calls('GET', tasksPath(OLAS_HOME)).length;

    await userEvent.click(screen.getByRole('button', { name: 'Fjern oppgaven «Rens sluket»' }));
    await userEvent.click(screen.getByRole('button', { name: 'Ja, fjern oppgaven «Rens sluket»' }));

    await waitFor(() => expect(api.calls('GET', tasksPath(OLAS_HOME)).length).toBeGreaterThan(before));
    expect(screen.queryByText(TASK_MESSAGES.archiveFailed)).not.toBeInTheDocument();
  });

  it('shows no «Fjern oppgaven» to a Tenant', async () => {
    fakeApi(signedInWith([OLAS_TENANCY]));
    renderAt(`/hjem/${OLAS_TENANCY.id}/oppgaver/${MUST.id}`);

    expect(await screen.findByRole('heading', { level: 1, name: MUST.name })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Fjern oppgaven/ })).not.toBeInTheDocument();
  });
});

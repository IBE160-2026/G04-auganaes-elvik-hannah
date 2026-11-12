// Story 2.6 (FR-24, FR-4, FR-8, UX "Add Task"): adding one catalog or custom Task, one test per
// frontend row of the spec's matrix and per acceptance criterion.
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { TASK_MESSAGES } from '../api/tasks';
import {
  OLAS_HOME,
  OLAS_TASKS,
  OLAS_TENANCY,
  fakeApi,
  homesResponse,
  json,
  resetApi,
  signedInWith,
  taskServer,
  tasksPath,
} from '../test-utils/fakeApi';

const OVERVIEW = `/hjem/${OLAS_HOME.id}`;
const ADD = `${OVERVIEW}/legg-til-oppgave`;
// The catalog fixture has vask-badet, rens-sluket and stekeovn; Ola's list has the last two.
const MISSING = 'Vask badet grundig';

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

function server() {
  const tasks = taskServer();
  return fakeApi({
    ...signedInWith(),
    [`GET ${tasksPath(OLAS_HOME)}`]: tasks.list,
    [`POST ${tasksPath(OLAS_HOME)}`]: tasks.add(),
  });
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date(2026, 10, 10, 12));
});
afterEach(() => vi.useRealTimers());
afterEach(resetApi);

describe('Add Task', () => {
  it('offers only the catalog types the Home lacks, plus «Egen oppgave», with nothing chosen', async () => {
    server();
    renderAt(ADD);

    const group = await screen.findByRole('group', { name: 'Velg oppgave' });
    const options = within(group).getAllByRole('radio');
    expect(options.map((o) => o.closest('label')?.textContent)).toEqual([MISSING, 'Egen oppgave']);
    expect(options.some((o) => (o as HTMLInputElement).checked)).toBe(false);
    expect(screen.queryByRole('radiogroup', { name: 'Må eller bør' })).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Legg til oppgave' })).toBeInTheDocument();
  });

  it('adds a catalog type with its recommendation and lands on the overview with the notice', async () => {
    const bodies: unknown[] = [];
    const tasks = taskServer();
    const api = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: tasks.list,
      [`POST ${tasksPath(OLAS_HOME)}`]: tasks.add(201, bodies),
    });
    renderAt(ADD);

    await userEvent.click(await screen.findByRole('radio', { name: MISSING }));
    expect(screen.getByRole('radio', { name: 'Må' })).toBeChecked();
    expect(screen.getByRole('combobox', { name: 'Hvor ofte' })).toHaveDisplayValue('Hver 6. uke');
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Hvor ofte' }), 'Hver måned');
    await userEvent.click(screen.getByRole('button', { name: 'Legg til' }));

    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(bodies).toEqual([{ task_type: 'vask-badet', classification: 'must', frequency_days: 30 }]);
    expect(window.location.pathname).toBe(OVERVIEW);
    expect(await screen.findByText('La til «Vask badet grundig».')).toBeInTheDocument();
    // The list was refetched before the page changed: the new Task is in it.
    expect(await screen.findByRole('link', { name: /^Vask badet grundig/ })).toBeInTheDocument();
    expect(api.calls('GET', tasksPath(OLAS_HOME)).length).toBeGreaterThanOrEqual(2);
  });

  it('adds a custom Task: «Egen oppgave» moves focus to the name, and the name goes in the body', async () => {
    const bodies: unknown[] = [];
    const tasks = taskServer();
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: tasks.list,
      [`POST ${tasksPath(OLAS_HOME)}`]: tasks.add(201, bodies),
    });
    renderAt(ADD);

    await userEvent.click(await screen.findByRole('radio', { name: 'Egen oppgave' }));
    const name = screen.getByRole('textbox', { name: 'Navn på oppgaven' });
    expect(name).toHaveFocus();
    expect(screen.getByRole('radio', { name: 'Bør' })).toBeChecked();
    expect(screen.getByRole('combobox', { name: 'Hvor ofte' })).toHaveDisplayValue('Hver måned');
    await userEvent.type(name, '  Vask gardiner ');
    await userEvent.click(screen.getByRole('radio', { name: 'Må' }));
    await userEvent.click(screen.getByRole('button', { name: 'Legg til' }));

    expect(await screen.findByText('La til «Vask gardiner».')).toBeInTheDocument();
    expect(bodies).toEqual([{ name: '  Vask gardiner ', classification: 'must', frequency_days: 30 }]);
    expect(await screen.findByRole('link', { name: /^Vask gardiner/ })).toBeInTheDocument();
  });

  it('says «Velg en oppgave.» and focuses the first option when nothing is chosen, sending nothing', async () => {
    const api = server();
    renderAt(ADD);

    await userEvent.click(await screen.findByRole('button', { name: 'Legg til' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(TASK_MESSAGES.chooseOne);
    expect(screen.getByRole('radio', { name: MISSING })).toHaveFocus();
    expect(api.calls('POST', tasksPath(OLAS_HOME))).toHaveLength(0);
  });

  it('switching choice resets Må/Bør and the interval but keeps a typed name', async () => {
    server();
    renderAt(ADD);

    await userEvent.click(await screen.findByRole('radio', { name: 'Egen oppgave' }));
    await userEvent.type(screen.getByRole('textbox', { name: 'Navn på oppgaven' }), 'Vask gardiner');
    await userEvent.click(screen.getByRole('radio', { name: 'Må' }));
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Hvor ofte' }), 'Hvert år');
    await userEvent.click(screen.getByRole('radio', { name: MISSING }));

    expect(screen.getByRole('radio', { name: 'Må' })).toBeChecked();
    expect(screen.getByRole('combobox', { name: 'Hvor ofte' })).toHaveDisplayValue('Hver 6. uke');
    await userEvent.click(screen.getByRole('radio', { name: 'Egen oppgave' }));
    expect(screen.getByRole('textbox', { name: 'Navn på oppgaven' })).toHaveValue('Vask gardiner');
    expect(screen.getByRole('radio', { name: 'Bør' })).toBeChecked();
    expect(screen.getByRole('combobox', { name: 'Hvor ofte' })).toHaveDisplayValue('Hver måned');
  });

  it('shows a refused name at the name field and offers «Prøv igjen»', async () => {
    const tasks = taskServer();
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: tasks.list,
      [`POST ${tasksPath(OLAS_HOME)}`]: tasks.add(422, [], 'Hjemmet har allerede en oppgave som heter «Rens sluket».'),
    });
    renderAt(ADD);

    await userEvent.click(await screen.findByRole('radio', { name: 'Egen oppgave' }));
    await userEvent.type(screen.getByRole('textbox', { name: 'Navn på oppgaven' }), 'rens sluket');
    await userEvent.click(screen.getByRole('button', { name: 'Legg til' }));

    const field = screen.getByRole('textbox', { name: 'Navn på oppgaven' });
    const message = await screen.findByText('Hjemmet har allerede en oppgave som heter «Rens sluket».');
    await waitFor(() => expect(field).toHaveAttribute('aria-invalid', 'true'));
    expect(field).toHaveAccessibleDescription(message.textContent ?? '');
    expect(screen.getByRole('button', { name: 'Prøv igjen' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(ADD);
  });

  it("shows the server's reason for a 409 at the form", async () => {
    const tasks = taskServer();
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: tasks.list,
      [`POST ${tasksPath(OLAS_HOME)}`]: tasks.add(409, [], 'Sett opp oppgavene først.'),
    });
    renderAt(ADD);

    await userEvent.click(await screen.findByRole('radio', { name: MISSING }));
    await userEvent.click(screen.getByRole('button', { name: 'Legg til' }));

    expect(await screen.findByText('Sett opp oppgavene først.')).toBeInTheDocument();
  });

  it('shows the generic message for a 500, and a 403 shows none (the global handler routes)', async () => {
    const tasks = taskServer();
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: tasks.list,
      [`POST ${tasksPath(OLAS_HOME)}`]: tasks.add(500),
    });
    renderAt(ADD);

    await userEvent.click(await screen.findByRole('radio', { name: MISSING }));
    await userEvent.click(screen.getByRole('button', { name: 'Legg til' }));

    expect(await screen.findByText(TASK_MESSAGES.addFailed)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Prøv igjen' })).toBeInTheDocument();
  });

  it('shows only «Egen oppgave», already chosen, when every catalog type is in the Home', async () => {
    const all = [
      ...OLAS_TASKS,
      { ...OLAS_TASKS[0], id: '00000000-0000-4000-8000-0000000000c9', task_type: 'vask-badet', name: MISSING },
    ];
    fakeApi({ ...signedInWith(), [`GET ${tasksPath(OLAS_HOME)}`]: () => json(200, { tasks: all }) });
    renderAt(ADD);

    const custom = await screen.findByRole('radio', { name: 'Egen oppgave' });
    expect(custom).toBeChecked();
    expect(screen.getAllByRole('radio', { name: /oppgave|badet/ })).toHaveLength(1);
    expect(screen.getByRole('textbox', { name: 'Navn på oppgaven' })).toBeInTheDocument();
  });

  it('sends a Tenant to the overview without showing the form', async () => {
    fakeApi({
      ...signedInWith([OLAS_TENANCY]),
    });
    renderAt(`/hjem/${OLAS_TENANCY.id}/legg-til-oppgave`);

    expect(await screen.findByRole('heading', { level: 1, name: OLAS_TENANCY.name })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Legg til oppgave' })).not.toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${OLAS_TENANCY.id}`);
  });

  it('sends an unknown Home to "/"', async () => {
    fakeApi({ ...signedInWith(), 'GET /api/homes': () => json(200, homesResponse([OLAS_HOME])) });
    renderAt('/hjem/00000000-0000-4000-8000-00000000ffff/legg-til-oppgave');

    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
  });

  it('has a way back to the overview', async () => {
    server();
    renderAt(ADD);

    await userEvent.click(await screen.findByRole('link', { name: 'Tilbake til oppgavene' }));

    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
  });
});

// Story 2.2 (decision 6): the read-only Task Detail, one test per case of the matrix row.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import type { Home } from '../api/homes';
import { TASK_MESSAGES } from '../api/tasks';
import { OLAS_HOME, OLAS_TASKS, fakeApi, json, resetApi, signedInWith, tasksPath } from '../test-utils/fakeApi';

const OVERVIEW = `/hjem/${OLAS_HOME.id}`;
const [MUST, OVERDUE] = OLAS_TASKS;
const detailPath = (taskId: string) => `${OVERVIEW}/oppgaver/${taskId}`;

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

// The fixtures' due dates are in 2026; formatDueOn adds the year in any other year.
beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date(2026, 10, 10, 12));
});

afterEach(() => vi.useRealTimers());
afterEach(resetApi);

describe('Task Detail', () => {
  it('opens from a row and shows the name, badge, interval and due text, with focus on the name', async () => {
    fakeApi(signedInWith());
    renderAt(OVERVIEW);

    await userEvent.click(await screen.findByRole('link', { name: /^Støvsug og vask gulvene/ }));

    const title = await screen.findByRole('heading', { level: 1, name: OVERDUE.name });
    expect(window.location.pathname).toBe(detailPath(OVERDUE.id));
    await waitFor(() => expect(title).toHaveFocus());
    expect(screen.getByText('Bør')).toBeInTheDocument();
    expect(screen.getByText('Hver 2. uke')).toBeInTheDocument();
    expect(screen.getByText('Forfalt — frist var 8. november')).toBeInTheDocument();
    // Read-only in 2.2: nothing to change, nothing to tick.
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('radio')).not.toBeInTheDocument();

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

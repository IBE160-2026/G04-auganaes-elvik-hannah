// Story 2.2 (FR-6, FR-21, UX-DR19/20/36/41): the Task Overview at /hjem/<id>, one test per
// frontend row of the spec's matrix and per acceptance criterion.
import { focusManager } from '@tanstack/react-query';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { HOME_MESSAGES, type Home } from '../api/homes';
import { lastHomeKey } from '../api/lastHome';
import { TASK_MESSAGES, type Task } from '../api/tasks';
import {
  OLA,
  OLAS_HOME,
  OLAS_TASKS,
  fakeApi,
  homesResponse,
  json,
  resetApi,
  signedInWith,
  tasksPath,
} from '../test-utils/fakeApi';
import { PULL_THRESHOLD } from './TaskOverview';

const PAGE = `/hjem/${OLAS_HOME.id}`;
const RENTAL: Home = {
  ...OLAS_HOME,
  id: '00000000-0000-4000-8000-0000000000b1',
  name: 'Storgata 12',
  type: 'landlord',
  role: 'landlord',
  can_leave: false,
};
const TENANCY: Home = { ...RENTAL, role: 'tenant', can_invite: false, can_set_up_tasks: false, has_tasks: false };
const NOTHING_DUE: Task[] = OLAS_TASKS.map((task) => ({ ...task, due_status: 'later', days_until_due: 30 }));

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

async function taskList() {
  return within(await screen.findByRole('region', { name: 'Oppgaver' }));
}

async function rows() {
  return (await (await taskList()).findAllByRole('link')).filter((link) => link.closest('li'));
}

// The fixtures' due dates are in 2026; formatDueOn adds the year in any other year.
beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date(2026, 10, 10, 12));
});

afterEach(() => vi.useRealTimers());
afterEach(resetApi);

describe('Task Overview', () => {
  it('lists every Må row above every Bør row, with the badge and the due state in words', async () => {
    fakeApi(signedInWith());
    renderAt(PAGE);

    const [must, overdue, soon] = await rows();
    expect(must).toHaveTextContent('Rens sluket');
    expect(within(must).getByText('Må')).toBeInTheDocument();
    expect(must).toHaveTextContent('Neste gang: 9. desember');
    expect(within(overdue).getByText('Bør')).toBeInTheDocument();
    const overdueText = within(overdue).getByText(/^Forfalt — frist var 8\. november/);
    expect(overdueText).toHaveClass('task-overview__due--overdue');
    expect(within(soon).getByText('Bør')).toBeInTheDocument();
    const soonText = within(soon).getByText('Snart forfall — i morgen');
    expect(soonText).toHaveClass('task-overview__due--due_soon');
    // Must first even though the Should rows are due earlier: the server's order, not re-sorted.
    expect([must, overdue, soon].map((row) => row.textContent?.split(/Må|Bør/)[0])).toEqual([
      'Rens sluket',
      'Støvsug og vask gulvene',
      'Vask stekeovnen',
    ]);
  });

  it('links each row to its Task Detail', async () => {
    fakeApi(signedInWith());
    renderAt(PAGE);

    const [must] = await rows();
    expect(must).toHaveAttribute('href', `${PAGE}/oppgaver/${OLAS_TASKS[0].id}`);
  });

  it('shows the Home name, the Role and «Medlemmer og invitasjon» in the header, with focus on the name', async () => {
    fakeApi(signedInWith());
    renderAt(PAGE);

    const title = await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name });
    await waitFor(() => expect(title).toHaveFocus());
    expect(screen.getByText('Husstandsmedlem')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Medlemmer og invitasjon' })).toHaveAttribute('href', `${PAGE}/medlemmer`);
    // One Home: nothing to switch to.
    expect(screen.queryByRole('link', { name: 'Bytt hjem' })).not.toBeInTheDocument();
    expect(screen.queryByText(/Velkommen hjem/)).not.toBeInTheDocument();
  });

  it('offers «Bytt hjem» to «Dine hjem» with two or more Homes', async () => {
    fakeApi(signedInWith([OLAS_HOME, RENTAL], ['landlord'], OLAS_HOME.id));
    renderAt(PAGE);

    await userEvent.click(await screen.findByRole('link', { name: 'Bytt hjem' }));

    const homes = await screen.findByRole('heading', { name: 'Dine hjem' });
    expect(window.location.pathname + window.location.hash).toBe('/innstillinger#dine-hjem');
    await waitFor(() => expect(homes).toHaveFocus());
  });

  it('tabs from the header through the rows, Må before Bør, then to the tab bar', async () => {
    fakeApi(signedInWith());
    renderAt(PAGE);

    const title = await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name });
    const [must, overdue, soon] = await rows();
    await waitFor(() => expect(title).toHaveFocus());
    const nav = screen.getByRole('navigation', { name: 'Hovedmeny' });

    const order = [
      screen.getByRole('link', { name: 'Medlemmer og invitasjon' }),
      screen.getByRole('button', { name: 'Oppdater' }),
      must,
      overdue,
      soon,
      within(nav).getByRole('link', { name: 'Oppgaver' }),
      within(nav).getByRole('link', { name: 'Innstillinger' }),
    ];
    for (const element of order) {
      await userEvent.tab();
      expect(element).toHaveFocus();
    }
  });

  it('shows 4 skeleton rows and no empty text while the tasks load', async () => {
    const server = fakeApi({ ...signedInWith(), [`GET ${tasksPath(OLAS_HOME)}`]: () => new Promise<Response>(() => {}) });
    renderAt(PAGE);

    await waitFor(() => expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(1));
    const skeleton = await screen.findByTestId('task-skeleton');
    expect(skeleton).toHaveAttribute('aria-hidden', 'true');
    expect(skeleton.querySelectorAll('li')).toHaveLength(4);
    expect(screen.queryByText(TASK_MESSAGES.nothingDueHousehold)).not.toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Oppgaver' })).toHaveAttribute('aria-busy', 'true');
  });

  it('shows the household empty text above the full list when nothing is due', async () => {
    fakeApi({ ...signedInWith(), [`GET ${tasksPath(OLAS_HOME)}`]: () => json(200, { tasks: NOTHING_DUE }) });
    renderAt(PAGE);

    const empty = await screen.findByText(TASK_MESSAGES.nothingDueHousehold);
    const all = await rows();
    expect(all).toHaveLength(OLAS_TASKS.length);
    expect(empty.compareDocumentPosition(all[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('shows a Landlord the landlord empty text when nothing is due', async () => {
    fakeApi({ ...signedInWith([RENTAL], ['landlord']), [`GET ${tasksPath(RENTAL)}`]: () => json(200, { tasks: NOTHING_DUE }) });
    renderAt(`/hjem/${RENTAL.id}`);

    expect(await screen.findByText(TASK_MESSAGES.nothingDueLandlord)).toBeInTheDocument();
    expect(screen.queryByText(TASK_MESSAGES.nothingDueHousehold)).not.toBeInTheDocument();
  });

  it('shows no empty text while something is overdue or due soon', async () => {
    fakeApi(signedInWith());
    renderAt(PAGE);

    await rows();
    expect(screen.queryByText(TASK_MESSAGES.nothingDueHousehold)).not.toBeInTheDocument();
  });

  it('shows a failed load inline with «Prøv igjen», keeping the header and the tab bar', async () => {
    let fail = true;
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: () => (fail ? json(500, { detail: 'x' }) : json(200, { tasks: OLAS_TASKS })),
    });
    renderAt(PAGE);

    expect(await (await taskList()).findByRole('alert')).toHaveTextContent(TASK_MESSAGES.loadFailed);
    expect(screen.getByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Hovedmeny' })).toBeInTheDocument();

    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv å hente oppgavene igjen' }));
    expect(await (await taskList()).findByText('Rens sluket')).toBeInTheDocument();
  });

  it('shows no inline error on a 403 and lets the refetched Homes route the user away', async () => {
    let member = true;
    fakeApi({
      ...signedInWith([OLAS_HOME, RENTAL], ['landlord']),
      'GET /api/homes': () => json(200, { homes: member ? [OLAS_HOME, RENTAL] : [RENTAL], allowed_types: ['landlord'], lived_in_home_id: null }),
      [`GET ${tasksPath(OLAS_HOME)}`]: () => {
        member = false;
        return json(403, { detail: 'Du har ikke tilgang til dette hjemmet.' });
      },
    });
    renderAt(PAGE);

    expect(await screen.findByRole('heading', { level: 1, name: RENTAL.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${RENTAL.id}`);
    expect(screen.queryByText(TASK_MESSAGES.loadFailed)).not.toBeInTheDocument();
  });

  it('refetches on «Oppdater» and announces «Oppdatert»', async () => {
    const server = fakeApi(signedInWith());
    renderAt(PAGE);
    await rows();

    await userEvent.click(screen.getByRole('button', { name: 'Oppdater' }));

    expect(await screen.findByText(TASK_MESSAGES.refreshed)).toHaveAttribute('aria-live', 'polite');
    expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(2);
  });

  it('stops the browser\'s own pull-to-reload while the list is shown, and restores it after', async () => {
    fakeApi(signedInWith());
    const view = renderAt(PAGE);
    await rows();

    expect(document.documentElement.style.overscrollBehaviorY).toBe('contain');
    view.unmount();
    expect(document.documentElement.style.overscrollBehaviorY).toBe('');
  });

  it('refetches on a pull from the top, and not on a short one', async () => {
    const server = fakeApi(signedInWith());
    renderAt(PAGE);
    await rows();
    const region = screen.getByRole('region', { name: 'Oppgaver' });

    fireEvent.touchStart(region, { touches: [{ clientY: 100 }] });
    fireEvent.touchMove(region, { touches: [{ clientY: 100 + PULL_THRESHOLD / 2 }] });
    fireEvent.touchEnd(region);
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(1);

    fireEvent.touchStart(region, { touches: [{ clientY: 100 }] });
    fireEvent.touchMove(region, { touches: [{ clientY: 100 + PULL_THRESHOLD }] });
    fireEvent.touchEnd(region);

    expect(await screen.findByText(TASK_MESSAGES.refreshed)).toBeInTheDocument();
    expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(2);
  });

  it('does not refresh on a pull that starts with the page scrolled down', async () => {
    const server = fakeApi(signedInWith());
    renderAt(PAGE);
    await rows();
    // jsdom has no scrollingElement; stand in one scrolled down, on the document only.
    Object.defineProperty(document, 'scrollingElement', { configurable: true, get: () => ({ scrollTop: 200 }) });
    try {
      const region = screen.getByRole('region', { name: 'Oppgaver' });
      fireEvent.touchStart(region, { touches: [{ clientY: 100 }] });
      fireEvent.touchMove(region, { touches: [{ clientY: 100 + PULL_THRESHOLD * 2 }] });
      fireEvent.touchEnd(region);
      await new Promise((resolve) => setTimeout(resolve, 20));
    } finally {
      // Back to Document.prototype's getter.
      delete (document as { scrollingElement?: unknown }).scrollingElement;
    }

    expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(1);
    expect(screen.queryByText(TASK_MESSAGES.refreshed)).not.toBeInTheDocument();
  });

  it('keeps the overview when a background refetch of the Homes fails', async () => {
    let fail = false;
    const server = fakeApi({
      ...signedInWith(),
      'GET /api/homes': () => (fail ? json(500, { detail: 'x' }) : json(200, homesResponse())),
    });
    renderAt(PAGE);
    await rows();

    fail = true;
    // A window-focus refetch, e.g. while offline.
    act(() => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
    });
    await waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(2));
    await new Promise((resolve) => setTimeout(resolve, 50));
    focusManager.setFocused(undefined);

    expect(screen.getByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(await rows()).toHaveLength(OLAS_TASKS.length);
    expect(screen.queryByText(HOME_MESSAGES.loadFailed)).not.toBeInTheDocument();
  });

  it('announces a failed refresh and keeps the list', async () => {
    let fail = false;
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: () => (fail ? json(500, { detail: 'x' }) : json(200, { tasks: OLAS_TASKS })),
    });
    renderAt(PAGE);
    await rows();

    fail = true;
    await userEvent.click(screen.getByRole('button', { name: 'Oppdater' }));

    expect(await screen.findByText(TASK_MESSAGES.refreshFailed)).toBeInTheDocument();
    expect(await rows()).toHaveLength(OLAS_TASKS.length);
  });

  it('sends a Home that is not the user\'s to "/", without fetching its tasks or recording it', async () => {
    const foreign = '00000000-0000-4000-8000-0000000000ff';
    const server = fakeApi(signedInWith());
    renderAt(`/hjem/${foreign}`);

    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(PAGE);
    expect(server.calls('GET', `/api/homes/${foreign}/tasks`)).toHaveLength(0);
    expect(localStorage.getItem(lastHomeKey(OLA.id))).toBe(OLAS_HOME.id);
  });

  it('sends a Household Member whose Home has no Tasks to Task Setup, without recording it', async () => {
    const home: Home = { ...OLAS_HOME, has_tasks: false };
    fakeApi(signedInWith([home]));
    renderAt(PAGE);

    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`${PAGE}/oppgaveoppsett`);
    expect(localStorage.getItem(lastHomeKey(OLA.id))).toBeNull();
  });

  it('tells a Tenant the Landlord has not set up tasks yet, fetches nothing and records the Home', async () => {
    const server = fakeApi(signedInWith([TENANCY]));
    renderAt(`/hjem/${TENANCY.id}`);

    expect(await screen.findByText(TASK_MESSAGES.tenantWaiting)).toBeInTheDocument();
    expect(screen.getByText('Leietaker')).toBeInTheDocument();
    expect(server.calls('GET', tasksPath(TENANCY))).toHaveLength(0);
    expect(localStorage.getItem(lastHomeKey(OLA.id))).toBe(TENANCY.id);
  });

  it('records the Home as last used once shown', async () => {
    fakeApi(signedInWith([OLAS_HOME, RENTAL], ['landlord']));
    renderAt(`/hjem/${RENTAL.id}`);

    await screen.findByRole('heading', { level: 1, name: RENTAL.name });
    await waitFor(() => expect(localStorage.getItem(lastHomeKey(OLA.id))).toBe(RENTAL.id));
  });

  it('makes «Husly» a link to "/", which opens the last used Home', async () => {
    fakeApi(signedInWith([OLAS_HOME, RENTAL], ['landlord']));
    renderAt(`/hjem/${RENTAL.id}`);
    await screen.findByRole('heading', { level: 1, name: RENTAL.name });

    await userEvent.click(within(screen.getByRole('banner')).getByRole('link', { name: 'Husly' }));

    await waitFor(() => expect(window.location.pathname).toBe(`/hjem/${RENTAL.id}`));
    expect(screen.getByRole('heading', { level: 1, name: RENTAL.name })).toBeInTheDocument();
  });
});

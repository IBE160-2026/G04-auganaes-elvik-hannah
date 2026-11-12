// Story 2.2 (FR-6, FR-21, UX-DR19/20/36/41): the Task Overview at /hjem/<id>, one test per
// frontend row of the spec's matrix and per acceptance criterion.
// Story 2.4 (FR-7, FR-17, UX-DR32/42): the checkbox on each card, its retries and roll-back.
// Story 2.6 (FR-24): «Legg til oppgave» and the list of a Home whose every Task is archived.
import { focusManager, onlineManager } from '@tanstack/react-query';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { HOME_MESSAGES, type Home } from '../api/homes';
import { lastHomeKey } from '../api/lastHome';
import { PUSH_MESSAGES } from '../api/push';
import { TASK_MESSAGES, type Task } from '../api/tasks';
import {
  DONE_BY_YOU_TODAY,
  OLA,
  OLAS_HOME,
  OLAS_TASKS,
  OLAS_TENANCY,
  completionPath,
  fakeApi,
  fakePush,
  homesResponse,
  json,
  resetApi,
  signedInWith,
  taskServer,
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
const TENANCY: Home = { ...RENTAL, role: 'tenant', can_invite: false, can_set_up_tasks: false, can_adjust_tasks: false, has_tasks: false };
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

  it('tabs from the header through each card\'s checkbox and row link, Må before Bør, then to the tab bar', async () => {
    fakeApi(signedInWith());
    renderAt(PAGE);

    const title = await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name });
    const [must, overdue, soon] = await rows();
    await waitFor(() => expect(title).toHaveFocus());
    const nav = screen.getByRole('navigation', { name: 'Hovedmeny' });

    const box = (name: string) => screen.getByRole('checkbox', { name: `Merk «${name}» som fullført` });
    const order = [
      screen.getByRole('link', { name: 'Medlemmer og invitasjon' }),
      // Story 2.6: a Household Member or the Landlord also gets «Legg til oppgave».
      screen.getByRole('link', { name: 'Legg til oppgave' }),
      screen.getByRole('button', { name: 'Oppdater' }),
      box('Rens sluket'),
      must,
      box('Støvsug og vask gulvene'),
      overdue,
      box('Vask stekeovnen'),
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

// Story 2.4: the self-checkoff on each card.
const [SLUKET, GULV, OVN] = OLAS_TASKS;

function box(name: string) {
  return screen.findByRole('checkbox', { name: `Merk «${name}» som fullført` });
}

function doneBox(name: string) {
  return screen.findByRole('checkbox', { name: `«${name}» er fullført` });
}

function card(name: string) {
  const row = screen.getByRole('link', { name: new RegExp(`^${name}`) });
  return row.closest('li') as HTMLElement;
}

describe('Self-checkoff (Story 2.4)', () => {
  it('completes a Task with one tap: checked, struck through, «Fullført i dag», one POST', async () => {
    const api = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV),
    });
    renderAt(PAGE);

    await userEvent.click(await box(GULV.name));

    const done = await doneBox(GULV.name);
    expect(done).toBeChecked();
    expect(done).toHaveAttribute('aria-disabled', 'true');
    expect(card(GULV.name).firstElementChild).toHaveClass('task-overview__card--done');
    expect(within(card(GULV.name)).getByText('Fullført i dag')).toBeInTheDocument();
    expect(within(card(GULV.name)).queryByText(/Forfalt/)).not.toBeInTheDocument();
    await waitFor(() => expect(server.calls('POST', completionPath(OLAS_HOME, GULV))).toHaveLength(1));
    // Only that card.
    expect(await box(SLUKET.name)).not.toBeChecked();
  });

  it('shows another Member\'s and a former Member\'s completion with the server\'s words', async () => {
    const tasks: Task[] = [
      { ...SLUKET, completion: { ...DONE_BY_YOU_TODAY, by: 'member', name: 'Jonas' } },
      { ...GULV, due_status: 'later', completion: { ...DONE_BY_YOU_TODAY, days_since: 1, by: 'former_member' } },
      OVN,
    ];
    fakeApi({ ...signedInWith(), [`GET ${tasksPath(OLAS_HOME)}`]: () => json(200, { tasks }) });
    renderAt(PAGE);

    expect(await doneBox(SLUKET.name)).toBeChecked();
    expect(within(card(SLUKET.name)).getByText('Fullført i dag av Jonas')).toBeInTheDocument();
    expect(within(card(GULV.name)).getByText('Fullført i går av tidligere medlem')).toBeInTheDocument();
    expect(await box(OVN.name)).not.toBeChecked();
  });

  it('ignores click and Space on a completed box and sends nothing (no undo)', async () => {
    const tasks: Task[] = [{ ...SLUKET, completion: DONE_BY_YOU_TODAY }, GULV, OVN];
    const server = fakeApi({ ...signedInWith(), [`GET ${tasksPath(OLAS_HOME)}`]: () => json(200, { tasks }) });
    renderAt(PAGE);

    const done = await doneBox(SLUKET.name);
    await userEvent.click(done);
    done.focus();
    await userEvent.keyboard(' ');

    expect(done).toBeChecked();
    expect(server.calls('POST', completionPath(OLAS_HOME, SLUKET))).toHaveLength(0);
  });

  it('sends one request for a double tap', async () => {
    let release = () => {};
    const gate = new Promise<void>((resolve) => (release = resolve));
    const api = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV, [200], gate),
    });
    renderAt(PAGE);

    await userEvent.dblClick(await box(GULV.name));
    release();

    expect(await doneBox(GULV.name)).toBeChecked();
    expect(server.calls('POST', completionPath(OLAS_HOME, GULV))).toHaveLength(1);
  });

  it('keeps the card checked through a refetch while the POST is pending', async () => {
    let release = () => {};
    const gate = new Promise<void>((resolve) => (release = resolve));
    const api = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV, [200], gate),
    });
    renderAt(PAGE);

    await userEvent.click(await box(GULV.name));
    await userEvent.click(screen.getByRole('button', { name: 'Oppdater' }));
    expect(await screen.findByText(TASK_MESSAGES.refreshed)).toBeInTheDocument();

    // The refetch says «not done»; the pending tick still wins.
    expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(2);
    expect(await doneBox(GULV.name)).toBeChecked();
    release();
    await waitFor(() => expect(within(card(GULV.name)).getByText('Fullført i dag')).toBeInTheDocument());
    expect(await doneBox(GULV.name)).toBeChecked();
  });

  it('retries a network error quietly: stays checked, no message, saved once', async () => {
    const api = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV, ['network', 200]),
    });
    renderAt(PAGE);

    await userEvent.click(await box(GULV.name));
    await waitFor(() => expect(server.calls('POST', completionPath(OLAS_HOME, GULV))).toHaveLength(1));
    expect(await doneBox(GULV.name)).toBeChecked();

    await waitFor(() => expect(server.calls('POST', completionPath(OLAS_HOME, GULV))).toHaveLength(2), { timeout: 3000 });
    expect(await doneBox(GULV.name)).toBeChecked();
    expect(screen.queryByText(TASK_MESSAGES.completeFailed(GULV.name))).not.toBeInTheDocument();
  });

  it('retries a 500 quietly and keeps the card checked', async () => {
    const api = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV, [500, 200]),
    });
    renderAt(PAGE);

    await userEvent.click(await box(GULV.name));

    await waitFor(() => expect(server.calls('POST', completionPath(OLAS_HOME, GULV))).toHaveLength(2), { timeout: 3000 });
    await waitFor(() => expect(within(card(GULV.name)).getByText('Fullført i dag')).toBeInTheDocument());
    expect(await doneBox(GULV.name)).toBeChecked();
    expect(screen.queryByText(TASK_MESSAGES.completeFailed(GULV.name))).not.toBeInTheDocument();
  });

  it('saves a tick made offline when the connection returns, without any action (AC 3)', async () => {
    const api = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV),
    });
    renderAt(PAGE);
    const unchecked = await box(GULV.name);

    act(() => onlineManager.setOnline(false));
    try {
      await userEvent.click(unchecked);
      expect(await doneBox(GULV.name)).toBeChecked();
      await new Promise((resolve) => setTimeout(resolve, 50));
      expect(server.calls('POST', completionPath(OLAS_HOME, GULV))).toHaveLength(0);
    } finally {
      act(() => onlineManager.setOnline(true));
    }

    await waitFor(() => expect(server.calls('POST', completionPath(OLAS_HOME, GULV))).toHaveLength(1));
    await waitFor(() => expect(within(card(GULV.name)).getByText('Fullført i dag')).toBeInTheDocument());
    expect(await doneBox(GULV.name)).toBeChecked();
  });

  it('rolls back only the refused card on a 404, refetches and shows a visible message', async () => {
    const api = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV, [404]),
      [`POST ${completionPath(OLAS_HOME, OVN)}`]: api.complete(OVN),
    });
    renderAt(PAGE);

    await userEvent.click(await box(OVN.name));
    expect(await doneBox(OVN.name)).toBeChecked();
    await userEvent.click(await box(GULV.name));

    const message = await within(card(GULV.name)).findByText(TASK_MESSAGES.completeFailed(GULV.name));
    expect(message).toHaveAttribute('aria-live', 'polite');
    expect(await box(GULV.name)).not.toBeChecked();
    expect(await doneBox(OVN.name)).toBeChecked();
    await waitFor(() => expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(2));
    expect(server.calls('POST', completionPath(OLAS_HOME, GULV))).toHaveLength(1);
  });

  it('shows the empty text when the only due Tasks are ticked', async () => {
    const api = taskServer([SLUKET, GULV]);
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV, [200], new Promise(() => {})),
    });
    renderAt(PAGE);
    await rows();
    expect(screen.queryByText(TASK_MESSAGES.nothingDueHousehold)).not.toBeInTheDocument();

    await userEvent.click(await box(GULV.name));

    expect(await screen.findByText(TASK_MESSAGES.nothingDueHousehold)).toBeInTheDocument();
  });

  // The server's stored completion reads «Fullført i går», so it is told apart from the pending
  // note «Fullført i dag».
  const SERVER_SAYS = { ...DONE_BY_YOU_TODAY, days_since: 1 };

  it('shows the server\'s completion once the tick is saved, without refetching the list', async () => {
    const api = taskServer(OLAS_TASKS, SERVER_SAYS);
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV),
    });
    renderAt(PAGE);

    await userEvent.click(await box(GULV.name));

    expect(await within(card(GULV.name)).findByText('Fullført i går')).toBeInTheDocument();
    expect(await doneBox(GULV.name)).toBeChecked();
    expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(1);
  });

  it('keeps the saved completion when a refetch started before the save answers after it', async () => {
    const api = taskServer(OLAS_TASKS, SERVER_SAYS);
    let releasePost = () => {};
    const postGate = new Promise<void>((resolve) => (releasePost = resolve));
    let releaseGet = () => {};
    let getGate: Promise<void> | null = null;
    const server = fakeApi({
      ...signedInWith(),
      // The answer is taken when the request arrives, then held: a stale «not done» list.
      [`GET ${tasksPath(OLAS_HOME)}`]: async (request) => {
        const answer = await api.list(request);
        if (getGate) await getGate;
        return answer;
      },
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV, [200], postGate),
    });
    renderAt(PAGE);

    await userEvent.click(await box(GULV.name));
    getGate = new Promise<void>((resolve) => (releaseGet = resolve));
    await userEvent.click(screen.getByRole('button', { name: 'Oppdater' }));
    await waitFor(() => expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(2));

    releasePost();
    expect(await within(card(GULV.name)).findByText('Fullført i går')).toBeInTheDocument();
    releaseGet();
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(within(card(GULV.name)).getByText('Fullført i går')).toBeInTheDocument();
    expect(await doneBox(GULV.name)).toBeChecked();
  });

  it('leaves a 403 to the global handler: no message, Homes and tasks refetched', async () => {
    const api = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: api.list,
      [`POST ${completionPath(OLAS_HOME, GULV)}`]: api.complete(GULV, [403]),
    });
    renderAt(PAGE);
    await rows();

    await userEvent.click(await box(GULV.name));

    await waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(2));
    await waitFor(() => expect(server.calls('GET', tasksPath(OLAS_HOME))).toHaveLength(2));
    expect(server.calls('POST', completionPath(OLAS_HOME, GULV))).toHaveLength(1);
    expect(await box(GULV.name)).not.toBeChecked();
    expect(screen.queryByText(/Vi fikk ikke krysset av/)).not.toBeInTheDocument();
  });
});

describe('Task Overview, add and an empty list (Story 2.6)', () => {
  it('shows «Legg til oppgave» in the header to whoever may adjust Tasks, and not to a Tenant', async () => {
    fakeApi(signedInWith());
    const { unmount } = renderAt(PAGE);

    const link = await screen.findByRole('link', { name: 'Legg til oppgave' });
    expect(link).toHaveAttribute('href', `${PAGE}/legg-til-oppgave`);
    unmount();
    resetApi();

    fakeApi(signedInWith([OLAS_TENANCY]));
    renderAt(`/hjem/${OLAS_TENANCY.id}`);
    expect(await screen.findByRole('link', { name: 'Medlemmer og invitasjon' })).toBeInTheDocument();
    expect(await screen.findByRole('link', { name: /^Rens sluket/ })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Legg til oppgave' })).not.toBeInTheDocument();
  });

  it('shows «Ingen oppgaver i hjemmet ennå.» with one «Legg til oppgave» when every Task is archived', async () => {
    fakeApi({ ...signedInWith(), [`GET ${tasksPath(OLAS_HOME)}`]: () => json(200, { tasks: [] }) });
    renderAt(PAGE);

    expect(await screen.findByText(TASK_MESSAGES.noTasks)).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Legg til oppgave' })).toHaveLength(1);
    expect(screen.queryByText(TASK_MESSAGES.nothingDueHousehold)).not.toBeInTheDocument();
    // Setup is not offered again: the guard keeps the user here.
    expect(window.location.pathname).toBe(PAGE);
  });

  it('tells a Tenant the Landlord has not set up Tasks, with no way to add', async () => {
    fakeApi({ ...signedInWith([OLAS_TENANCY]), [`GET ${tasksPath(OLAS_TENANCY)}`]: () => json(200, { tasks: [] }) });
    renderAt(`/hjem/${OLAS_TENANCY.id}`);

    expect(await screen.findByText(TASK_MESSAGES.tenantWaiting)).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Legg til oppgave' })).not.toBeInTheDocument();
    expect(screen.queryByText(TASK_MESSAGES.noTasks)).not.toBeInTheDocument();
  });
});

// Story 3.1 (UX-DR31): one dismissible note when push is blocked and something is due.
describe('Task Overview, blocked push note', () => {
  const NOTE = PUSH_MESSAGES.deniedNote;

  it('shows one inline note, not a modal, when push is denied and a Task is overdue or due soon', async () => {
    fakePush({ permission: 'denied' });
    fakeApi(signedInWith());
    renderAt(PAGE);

    expect(await screen.findByText(NOTE)).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.getAllByText(NOTE)).toHaveLength(1);
  });

  it.each([
    ['push is allowed', 'granted', OLAS_TASKS],
    ['push is not asked yet', 'default', OLAS_TASKS],
    ['nothing is due, even when push is denied', 'denied', NOTHING_DUE],
  ] as const)('shows no note when %s', async (_label, permission, tasks) => {
    fakePush({ permission });
    fakeApi({ ...signedInWith(), [`GET ${tasksPath(OLAS_HOME)}`]: () => json(200, { tasks }) });
    renderAt(PAGE);

    await taskList();
    expect(screen.queryByText(NOTE)).toBeNull();
  });

  it('shows no note where the browser cannot push at all', async () => {
    fakeApi(signedInWith());
    renderAt(PAGE);

    await taskList();
    expect(screen.queryByText(NOTE)).toBeNull();
  });

  it('stays closed after «Lukk», also on the next visit', async () => {
    fakePush({ permission: 'denied' });
    fakeApi(signedInWith());
    const first = renderAt(PAGE);

    await userEvent.click(await screen.findByRole('button', { name: PUSH_MESSAGES.dismissNote }));
    expect(screen.queryByText(NOTE)).toBeNull();

    first.unmount();
    renderAt(PAGE);
    await taskList();
    expect(screen.queryByText(NOTE)).toBeNull();
  });
});

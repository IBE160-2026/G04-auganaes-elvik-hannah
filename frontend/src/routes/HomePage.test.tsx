// Story 1.3 (FR-1, FR-3): when "/" shows the Home page and when it sends a user to Create Home.
// Story 2.1 (FR-4, FR-8, decisions 1, 7 and 8): the minimal task list, the redirect to Task Setup
// for a Home without Tasks, the Tenant's waiting text and «Sett opp oppgaver» in «Dine hjem».
import { focusManager } from '@tanstack/react-query';
import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { HOME_MESSAGES, type Home } from '../api/homes';
import { TASK_MESSAGES } from '../api/tasks';
import {
  OLAS_HOME,
  OLAS_TASKS,
  fakeApi,
  homesResponse,
  json,
  resetApi,
  signedInWith,
  tasksPath,
} from '../test-utils/fakeApi';

const RENTAL_1: Home = { ...OLAS_HOME, id: '00000000-0000-4000-8000-0000000000b1', name: 'Storgata 1', type: 'landlord', role: 'landlord', can_leave: false };
const RENTAL_2: Home = { ...RENTAL_1, id: '00000000-0000-4000-8000-0000000000b2', name: 'Storgata 2' };

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

afterEach(resetApi);

describe('Home page', () => {
  it('sends a user to Create Home once the list has loaded empty', async () => {
    fakeApi(signedInWith([], ['household', 'landlord']));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/nytt-hjem');
  });

  it('waits while the list is loading and never redirects', async () => {
    const server = fakeApi({ ...signedInWith(), 'GET /api/homes': () => new Promise<Response>(() => {}) });
    renderAt('/');

    // Past the session gate's own "Laster …": the Homes request is out and has not answered.
    await waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(1));
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(screen.getByRole('status')).toHaveTextContent('Laster …');
    expect(window.location.pathname).toBe('/');
  });

  it('shows a failed load inline with a retry, without redirecting', async () => {
    let fail = true;
    fakeApi({
      ...signedInWith(),
      'GET /api/homes': () => (fail ? json(500, { detail: 'x' }) : json(200, homesResponse())),
    });
    renderAt('/');

    expect(await screen.findByRole('alert')).toHaveTextContent(HOME_MESSAGES.loadFailed);
    expect(window.location.pathname).toBe('/');
    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));
    expect(await screen.findByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();
  });

  it('keeps showing the Home when a background refetch fails', async () => {
    let fail = false;
    const server = fakeApi({
      ...signedInWith(),
      'GET /api/homes': () => (fail ? json(500, { detail: 'x' }) : json(200, homesResponse())),
    });
    renderAt('/');
    expect(await screen.findByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();

    fail = true;
    // A window-focus refetch, e.g. while offline.
    act(() => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
    });
    await waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(2));
    await new Promise((resolve) => setTimeout(resolve, 50));
    focusManager.setFocused(undefined);

    expect(screen.getByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();
    expect(screen.queryByText(HOME_MESSAGES.loadFailed)).not.toBeInTheDocument();
  });

  it('shows a Member the Home, type and Role, no Homes list, and "Opprett nytt hjem"', async () => {
    // Story 1.9: a Household Member may create a Landlord Home.
    fakeApi(signedInWith([OLAS_HOME], ['landlord'], OLAS_HOME.id));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Kollektivet' })).toBeInTheDocument();
    expect(screen.getByText('Husstand')).toBeInTheDocument();
    expect(screen.getByText('Husstandsmedlem')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Dine hjem' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Logg ut' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('link', { name: 'Opprett nytt hjem' }));
    expect(await screen.findByRole('heading', { name: 'Opprett ny utleiebolig' })).toBeInTheDocument();
    expect(
      screen.getByText('Du blir utleier for den nye boligen. Medlemskapet ditt i «Kollektivet» endres ikke.'),
    ).toBeInTheDocument();
  });

  it('shows no create link and sends /nytt-hjem back to "/" while nothing is offered', async () => {
    // Only a cache placeholder or a fixture is empty: the server always offers a Landlord Home.
    fakeApi(signedInWith([OLAS_HOME], []));
    renderAt('/nytt-hjem');

    expect(await screen.findByRole('heading', { name: 'Kollektivet' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
    expect(screen.queryByRole('link', { name: 'Opprett nytt hjem' })).not.toBeInTheDocument();
  });

  it('shows a Landlord the newest Home, all their Homes and "Opprett nytt hjem"', async () => {
    fakeApi(signedInWith([RENTAL_2, RENTAL_1], ['household', 'landlord']));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Storgata 2' })).toBeInTheDocument();
    expect(screen.getByText('Utleiebolig')).toBeInTheDocument();
    const list = within(screen.getByRole('region', { name: 'Dine hjem' })).getByRole('list');
    expect(list).toHaveTextContent('Storgata 2');
    expect(list).toHaveTextContent('Storgata 1');

    await userEvent.click(screen.getByRole('link', { name: 'Opprett nytt hjem' }));
    // Story 1.9: a Landlord who lives in no Home is offered both types.
    expect(await screen.findByRole('heading', { name: 'Opprett nytt hjem' })).toBeInTheDocument();
    expect(screen.getAllByRole('radio')).toHaveLength(2);
    await waitFor(() => expect(window.location.pathname).toBe('/nytt-hjem'));
  });
});

describe('Home page tasks (Story 2.1)', () => {
  const NO_TASKS: Home = { ...OLAS_HOME, has_tasks: false };
  const TENANCY: Home = {
    ...OLAS_HOME,
    name: 'Storgata 12',
    type: 'landlord',
    role: 'tenant',
    can_invite: false,
    can_set_up_tasks: false,
    has_tasks: false,
  };

  it('lists each task with its name, Må/Bør badge, interval and next date', async () => {
    fakeApi(signedInWith());
    renderAt('/');

    const section = await screen.findByRole('region', { name: 'Oppgaver' });
    const rows = await within(section).findAllByRole('listitem');
    expect(rows).toHaveLength(OLAS_TASKS.length);
    expect(rows[0]).toHaveTextContent('Rens sluket');
    expect(within(rows[0]).getByText('Må')).toBeInTheDocument();
    expect(rows[0]).toHaveTextContent('Hver måned');
    expect(rows[0]).toHaveTextContent(/Neste gang: 9\. desember/);
    expect(within(rows[1]).getByText('Bør')).toBeInTheDocument();
    expect(rows[1]).toHaveTextContent('Hver 2. uke');
    expect(rows[1]).toHaveTextContent(/Neste gang: 23\. november/);
  });

  it('sends a Household Member whose Home has no Tasks to Task Setup', async () => {
    fakeApi(signedInWith([NO_TASKS]));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${NO_TASKS.id}/oppgaveoppsett`);
  });

  it('sends a Landlord whose newest Home has no Tasks to Task Setup', async () => {
    const rental: Home = { ...RENTAL_1, has_tasks: false };
    fakeApi(signedInWith([rental], ['landlord']));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${rental.id}/oppgaveoppsett`);
  });

  it('tells a Tenant the Landlord has not set up tasks yet, and stays', async () => {
    const server = fakeApi(signedInWith([TENANCY]));
    renderAt('/');

    expect(await screen.findByText(TASK_MESSAGES.tenantWaiting)).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
    // Nothing to list, so nothing is fetched.
    expect(server.calls('GET', tasksPath(TENANCY))).toHaveLength(0);
  });

  it('offers «Sett opp oppgaver» for a Landlord\'s older Home without Tasks, and opens its setup', async () => {
    const older: Home = { ...RENTAL_1, has_tasks: false };
    fakeApi(signedInWith([RENTAL_2, older], ['landlord']));
    renderAt('/');

    const homesList = await screen.findByRole('region', { name: 'Dine hjem' });
    expect(within(homesList).getAllByRole('link', { name: /^Sett opp oppgaver/ })).toHaveLength(1);
    await userEvent.click(within(homesList).getByRole('link', { name: 'Sett opp oppgaver for Storgata 1' }));

    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${older.id}/oppgaveoppsett`);
    expect(screen.getByText(/Storgata 1»/)).toBeInTheDocument();
  });

  it('shows a failed tasks load in the task section with a retry, and keeps the rest of the page', async () => {
    let fail = true;
    fakeApi({
      ...signedInWith(),
      [`GET ${tasksPath(OLAS_HOME)}`]: () => (fail ? json(500, { detail: 'x' }) : json(200, { tasks: OLAS_TASKS })),
    });
    renderAt('/');

    const section = await screen.findByRole('region', { name: 'Oppgaver' });
    expect(await within(section).findByRole('alert')).toHaveTextContent(TASK_MESSAGES.loadFailed);
    expect(screen.getByRole('link', { name: 'Medlemmer og invitasjon' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Logg ut' })).toBeInTheDocument();

    fail = false;
    await userEvent.click(within(section).getByRole('button', { name: 'Prøv å hente oppgavene igjen' }));
    expect(await within(section).findByText('Rens sluket')).toBeInTheDocument();
  });
});

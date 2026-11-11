// Story 1.3 (FR-1, FR-3): "/" sends a user without a Home to Create Home.
// Story 2.2 (decisions 3 and 12): "/" only redirects, to the most recently used Home on this
// device, else the Home the user lives in, else the first.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { HOME_MESSAGES, type Home } from '../api/homes';
import { lastHomeKey } from '../api/lastHome';
import { OLA, OLAS_HOME, fakeApi, homesResponse, json, resetApi, signedInWith } from '../test-utils/fakeApi';

const RENTAL_1: Home = { ...OLAS_HOME, id: '00000000-0000-4000-8000-0000000000b1', name: 'Storgata 1', type: 'landlord', role: 'landlord', can_leave: false };
const RENTAL_2: Home = { ...RENTAL_1, id: '00000000-0000-4000-8000-0000000000b2', name: 'Storgata 2' };

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

afterEach(resetApi);

describe('"/"', () => {
  it('sends a user to Create Home once the list has loaded empty, without a tab bar', async () => {
    fakeApi(signedInWith([], ['household', 'landlord']));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/nytt-hjem');
    expect(screen.queryByRole('navigation', { name: 'Hovedmeny' })).not.toBeInTheDocument();
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
    expect(screen.queryByRole('navigation', { name: 'Hovedmeny' })).not.toBeInTheDocument();
    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));
    expect(await screen.findByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}`);
  });

  it('opens the most recently used Home, replacing "/" in the history', async () => {
    localStorage.setItem(lastHomeKey(OLA.id), RENTAL_1.id);
    fakeApi(signedInWith([RENTAL_2, RENTAL_1], ['landlord']));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Storgata 1' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${RENTAL_1.id}`);
  });

  it('falls back to the Home the user lives in when the stored one is gone', async () => {
    localStorage.setItem(lastHomeKey(OLA.id), 'gone');
    fakeApi(signedInWith([RENTAL_1, OLAS_HOME], ['landlord'], OLAS_HOME.id));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}`);
  });

  it('falls back to the first Home when nothing is stored and the user lives in none', async () => {
    fakeApi(signedInWith([RENTAL_2, RENTAL_1], ['landlord']));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Storgata 2' })).toBeInTheDocument();
  });

  it('opens a Landlord\'s Home without Tasks in Task Setup', async () => {
    const rental: Home = { ...RENTAL_1, has_tasks: false };
    fakeApi(signedInWith([rental], ['landlord']));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${rental.id}/oppgaveoppsett`);
  });

  it('sends /nytt-hjem back through "/" to the Home while nothing is offered', async () => {
    // Only a cache placeholder or a fixture is empty: the server always offers a Landlord Home.
    fakeApi(signedInWith([OLAS_HOME], []));
    renderAt('/nytt-hjem');

    expect(await screen.findByRole('heading', { name: 'Kollektivet' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}`);
  });
});

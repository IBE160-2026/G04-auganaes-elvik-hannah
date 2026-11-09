// Story 1.3 (FR-1, FR-3): when "/" shows the Home page and when it sends a user to Create Home.
import { focusManager } from '@tanstack/react-query';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { HOME_MESSAGES, type Home } from '../api/homes';
import { OLAS_HOME, fakeApi, homesResponse, json, resetApi, signedInWith } from '../test-utils/fakeApi';

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

  it('shows a Member the Home, type and Role, and neither a Homes list nor a create link', async () => {
    fakeApi(signedInWith([OLAS_HOME], []));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Kollektivet' })).toBeInTheDocument();
    expect(screen.getByText('Husstand')).toBeInTheDocument();
    expect(screen.getByText('Husstandsmedlem')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Dine hjem' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Opprett nytt hjem' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Logg ut' })).toBeInTheDocument();
  });

  it('sends a Member who opens /nytt-hjem directly back to the Home page', async () => {
    fakeApi(signedInWith([OLAS_HOME], []));
    renderAt('/nytt-hjem');

    expect(await screen.findByRole('heading', { name: 'Kollektivet' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
  });

  it('shows a Landlord the newest Home, all their Homes and "Opprett nytt hjem"', async () => {
    fakeApi(signedInWith([RENTAL_2, RENTAL_1], ['landlord']));
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Storgata 2' })).toBeInTheDocument();
    expect(screen.getByText('Utleiebolig')).toBeInTheDocument();
    const list = screen.getByRole('list');
    expect(list).toHaveTextContent('Storgata 2');
    expect(list).toHaveTextContent('Storgata 1');

    await userEvent.click(screen.getByRole('link', { name: 'Opprett nytt hjem' }));
    expect(await screen.findByRole('heading', { name: 'Opprett ny utleiebolig' })).toBeInTheDocument();
    await waitFor(() => expect(window.location.pathname).toBe('/nytt-hjem'));
  });
});

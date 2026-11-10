// Story 2.2 (decision 4): Settings/Profile at /innstillinger, and switching Homes from «Dine hjem».
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import type { Home } from '../api/homes';
import { OLA, OLAS_HOME, fakeApi, json, resetApi, signedInWith } from '../test-utils/fakeApi';

const STORGATA: Home = {
  ...OLAS_HOME,
  id: '00000000-0000-4000-8000-0000000000b1',
  name: 'Storgata 12',
  type: 'landlord',
  role: 'landlord',
  can_leave: false,
};
const NEW_RENTAL: Home = { ...STORGATA, id: '00000000-0000-4000-8000-0000000000b2', name: 'Storgata 14', has_tasks: false };

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

function homesList() {
  return within(screen.getByRole('region', { name: 'Dine hjem' }));
}

afterEach(resetApi);

describe('Settings', () => {
  it('shows the name and e-mail, with focus on the heading', async () => {
    fakeApi(signedInWith());
    renderAt('/innstillinger');

    const title = await screen.findByRole('heading', { level: 1, name: 'Innstillinger' });
    await waitFor(() => expect(title).toHaveFocus());
    expect(screen.getByText(OLA.name)).toBeInTheDocument();
    expect(screen.getByText(OLA.email)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Logg ut' })).toBeInTheDocument();
  });

  it('lists every Home with its Role, «Medlemmer», and «Sett opp oppgaver» only where it applies', async () => {
    fakeApi(signedInWith([OLAS_HOME, STORGATA, NEW_RENTAL], ['landlord'], OLAS_HOME.id));
    renderAt('/innstillinger');

    await screen.findByRole('region', { name: 'Dine hjem' });
    const items = homesList().getAllByRole('listitem');
    expect(items).toHaveLength(3);
    expect(items[0]).toHaveTextContent('Husstandsmedlem');
    expect(items[1]).toHaveTextContent('Utleier');
    expect(within(items[0]).getByRole('link', { name: 'Kollektivet' })).toHaveAttribute('href', `/hjem/${OLAS_HOME.id}`);
    expect(homesList().getByRole('link', { name: 'Medlemmer og invitasjon for Storgata 12' })).toHaveAttribute(
      'href',
      `/hjem/${STORGATA.id}/medlemmer`,
    );
    expect(homesList().getAllByRole('link', { name: /^Sett opp oppgaver/ })).toHaveLength(1);
    expect(homesList().getByRole('link', { name: 'Sett opp oppgaver for Storgata 14' })).toHaveAttribute(
      'href',
      `/hjem/${NEW_RENTAL.id}/oppgaveoppsett`,
    );
  });

  it('offers «Opprett nytt hjem» only when the server allows a type', async () => {
    fakeApi(signedInWith([OLAS_HOME], ['landlord'], OLAS_HOME.id));
    renderAt('/innstillinger');
    expect(await screen.findByRole('link', { name: 'Opprett nytt hjem' })).toHaveAttribute('href', '/nytt-hjem');
    cleanup();
    resetApi();

    fakeApi(signedInWith([OLAS_HOME], []));
    renderAt('/innstillinger');
    await screen.findByRole('region', { name: 'Dine hjem' });
    expect(screen.queryByRole('link', { name: 'Opprett nytt hjem' })).not.toBeInTheDocument();
  });

  it('sends a user without a Home to Create Home', async () => {
    fakeApi(signedInWith([], ['household', 'landlord']));
    renderAt('/innstillinger');

    expect(await screen.findByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
  });

  it('marks «Innstillinger» as the current tab, and «Oppgaver» opens the last used Home', async () => {
    fakeApi(signedInWith([OLAS_HOME, STORGATA], ['landlord'], OLAS_HOME.id));
    renderAt(`/hjem/${STORGATA.id}`);
    await screen.findByRole('heading', { level: 1, name: STORGATA.name });

    const nav = screen.getByRole('navigation', { name: 'Hovedmeny' });
    await userEvent.click(within(nav).getByRole('link', { name: 'Innstillinger' }));
    await screen.findByRole('heading', { level: 1, name: 'Innstillinger' });

    expect(within(nav).getByRole('link', { name: 'Innstillinger' })).toHaveAttribute('aria-current', 'page');
    const tasks = within(nav).getByRole('link', { name: 'Oppgaver' });
    expect(tasks).not.toHaveAttribute('aria-current');
    expect(tasks).toHaveAttribute('href', `/hjem/${STORGATA.id}`);
  });

  it('switches Homes: opening «Storgata 12» from «Dine hjem» makes "/" open it after a reload', async () => {
    // Kari has created a Household Home and lives there; Storgata 12 is her rental.
    const handlers = signedInWith([OLAS_HOME, STORGATA], ['landlord'], OLAS_HOME.id);
    fakeApi(handlers);
    renderAt('/');
    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('link', { name: 'Bytt hjem' }));
    await screen.findByRole('region', { name: 'Dine hjem' });
    await userEvent.click(homesList().getByRole('link', { name: 'Storgata 12' }));
    expect(await screen.findByRole('heading', { level: 1, name: STORGATA.name })).toBeInTheDocument();

    // A reload: a fresh app and query cache, same device.
    cleanup();
    fakeApi({ ...handlers, 'GET /api/auth/me': () => json(200, OLA) });
    renderAt('/');

    expect(await screen.findByRole('heading', { level: 1, name: STORGATA.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${STORGATA.id}`);
  });
});

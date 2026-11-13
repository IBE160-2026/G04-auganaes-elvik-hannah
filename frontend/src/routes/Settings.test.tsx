// Story 2.2 (decision 4): Settings/Profile at /innstillinger, and switching Homes from «Dine hjem».
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import type { Home } from '../api/homes';
import { PUSH_MESSAGES } from '../api/push';
import { OLA, OLAS_HOME, PUSH_ENDPOINT, fakeApi, fakePush, json, pushServer, resetApi, signedInWith } from '../test-utils/fakeApi';

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

// Story 3.1 (FR-10, UX-DR31): «Varsler» shows the permission and registers this device.
describe('Settings, Varsler', () => {
  function pushSection() {
    return within(screen.getByRole('region', { name: 'Varsler' }));
  }

  it.each([
    ['default', PUSH_MESSAGES.default],
    ['denied', PUSH_MESSAGES.denied],
  ] as const)('says plainly that the permission is %s', async (permission, text) => {
    fakePush({ permission });
    fakeApi({ ...signedInWith(), ...pushServer() });
    renderAt('/innstillinger');

    await screen.findByRole('region', { name: 'Varsler' });
    expect(await pushSection().findByText(text)).toBeInTheDocument();
    expect(pushSection().queryByRole('button', { name: PUSH_MESSAGES.enable }) !== null).toBe(permission === 'default');
  });

  it('says push is unsupported without an active service worker, and never waits for one', async () => {
    fakePush({ worker: false });
    fakeApi({ ...signedInWith(), ...pushServer() });
    renderAt('/innstillinger');

    await screen.findByRole('region', { name: 'Varsler' });
    expect(await pushSection().findByText(PUSH_MESSAGES.unsupported)).toBeInTheDocument();
    expect(pushSection().queryByRole('button')).toBeNull();
  });

  it('asks for permission only after the tap, then stores this device with its keys', async () => {
    const push = fakePush({ permission: 'default', answer: 'granted' });
    const puts: unknown[] = [];
    fakeApi({ ...signedInWith(), ...pushServer(puts) });
    renderAt('/innstillinger');

    await screen.findByRole('region', { name: 'Varsler' });
    await pushSection().findByText(PUSH_MESSAGES.default);
    expect(push.requestPermission).not.toHaveBeenCalled();
    await userEvent.click(pushSection().getByRole('button', { name: PUSH_MESSAGES.enable }));

    expect(await pushSection().findByText(PUSH_MESSAGES.granted)).toBeInTheDocument();
    expect(push.subscribe).toHaveBeenCalledOnce();
    expect(puts).toEqual([{ endpoint: PUSH_ENDPOINT, p256dh: 'k1', auth: 'a1' }]);
  });

  it('keeps the status and offers «Prøv igjen» when the subscription fails', async () => {
    fakePush({ permission: 'default', answer: 'granted', subscribeFails: true });
    fakeApi({ ...signedInWith(), ...pushServer() });
    renderAt('/innstillinger');

    await userEvent.click(await screen.findByRole('button', { name: PUSH_MESSAGES.enable }));
    expect(await screen.findByRole('alert')).toHaveTextContent(PUSH_MESSAGES.failed);
    expect(pushSection().getByRole('button', { name: PUSH_MESSAGES.retry })).toBeInTheDocument();
  });

  it('registers this device silently when permission is already granted', async () => {
    const push = fakePush({ permission: 'granted', subscribed: true });
    const puts: unknown[] = [];
    fakeApi({ ...signedInWith(), ...pushServer(puts) });
    renderAt('/innstillinger');

    await waitFor(() => expect(puts).toEqual([{ endpoint: PUSH_ENDPOINT, p256dh: 'k1', auth: 'a1' }]));
    expect(push.requestPermission).not.toHaveBeenCalled();
  });

  it('removes this device on the server before signing out, and still signs out if that fails', async () => {
    fakePush({ permission: 'granted', subscribed: true });
    const deletes: unknown[] = [];
    const api = fakeApi({
      ...signedInWith(),
      ...pushServer(),
      'DELETE /api/push/subscriptions': async (request) => {
        deletes.push(await request.json());
        throw new TypeError('Failed to fetch');
      },
    });
    renderAt('/innstillinger');

    await userEvent.click(await screen.findByRole('button', { name: 'Logg ut' }));

    await waitFor(() => expect(api.calls('POST', '/api/auth/logout')).toHaveLength(1));
    expect(deletes).toEqual([{ endpoint: PUSH_ENDPOINT }]);
    const order = api.requests.map((r) => `${r.method} ${new URL(r.url).pathname}`);
    expect(order.indexOf('DELETE /api/push/subscriptions')).toBeLessThan(order.indexOf('POST /api/auth/logout'));
    expect(await screen.findByRole('heading', { name: /Logg inn/ })).toBeInTheDocument();
  });

  it('subscribes this browser when permission is granted but it holds no subscription yet', async () => {
    const push = fakePush({ permission: 'granted', subscribed: false });
    const puts: unknown[] = [];
    fakeApi({ ...signedInWith(), ...pushServer(puts) });
    renderAt('/innstillinger');

    await waitFor(() => expect(puts).toEqual([{ endpoint: PUSH_ENDPOINT, p256dh: 'k1', auth: 'a1' }]));
    expect(push.subscribe).toHaveBeenCalledOnce();
    expect(push.requestPermission).not.toHaveBeenCalled();
  });

  it('shows a failed silent registration, and clears it when «Prøv igjen» works', async () => {
    fakePush({ permission: 'granted', subscribed: true });
    let status: 204 | 500 = 500;
    fakeApi({
      ...signedInWith(),
      ...pushServer(),
      'PUT /api/push/subscriptions': () =>
        status === 204 ? new Response(null, { status: 204 }) : json(500, { detail: 'nei' }),
    });
    renderAt('/innstillinger');

    expect(await screen.findByRole('alert')).toHaveTextContent(PUSH_MESSAGES.failed);
    status = 204;
    await userEvent.click(pushSection().getByRole('button', { name: PUSH_MESSAGES.retry }));
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
  });
});

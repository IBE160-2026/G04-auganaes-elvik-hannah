// Story 1.10 (FR-25): «Slett konto» under Settings, one test per row of the spec's matrix that the
// frontend owns. Each test names the line it guards.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { DELETE_ACCOUNT_MESSAGES } from '../api/auth';
import { lastHomeKey } from '../api/lastHome';
import { OLA, OLAS_HOME, fakeApi, fakePush, json, resetApi, signedInWith } from '../test-utils/fakeApi';

const PATH = '/api/auth/delete-account';

function renderSettings() {
  window.history.pushState({}, '', '/innstillinger');
  return render(<App />);
}

async function openConfirmation() {
  await userEvent.click(await screen.findByRole('button', { name: 'Slett konto' }));
  return screen.getByLabelText(DELETE_ACCOUNT_MESSAGES.passwordLabel);
}

afterEach(resetApi);

describe('Slett konto', () => {
  it('sends nothing until the password is given and «Ja, slett kontoen» is pressed', async () => {
    // Guards the reveal step: the first button only opens the confirmation.
    const server = fakeApi({ ...signedInWith(), [`POST ${PATH}`]: () => json(204) });
    renderSettings();

    const field = await openConfirmation();

    expect(field).toHaveFocus();
    expect(screen.getByText(/kan ikke angres/)).toBeInTheDocument();
    expect(server.calls('POST', PATH)).toHaveLength(0);
  });

  it('asks for the password when it is empty, and sends nothing', async () => {
    // Guards the `password === ''` check in submit.
    const server = fakeApi({ ...signedInWith(), [`POST ${PATH}`]: () => json(204) });
    renderSettings();
    await openConfirmation();

    await userEvent.click(screen.getByRole('button', { name: 'Ja, slett kontoen' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(DELETE_ACCOUNT_MESSAGES.passwordMissing);
    expect(server.calls('POST', PATH)).toHaveLength(0);
  });

  it('shows the server’s text for a wrong password and keeps the session', async () => {
    // Guards that a failure does not clear the session (setSession(null) only after ok).
    fakeApi({
      ...signedInWith(),
      [`POST ${PATH}`]: () => json(400, { detail: 'Passordet stemmer ikke.' }),
    });
    renderSettings();
    const field = await openConfirmation();
    await userEvent.type(field, 'feil passord 1');

    await userEvent.click(screen.getByRole('button', { name: 'Ja, slett kontoen' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Passordet stemmer ikke.');
    expect(screen.getByRole('heading', { name: 'Innstillinger' })).toBeInTheDocument();
  });

  it('shows the server’s text for a Landlord who still has Tenants', async () => {
    // Guards the pass-through of the 409 text (passThrough: 'any').
    const text = 'Du må fjerne leietakerne før du kan slette kontoen. Gjelder: Storgata 12.';
    fakeApi({ ...signedInWith(), [`POST ${PATH}`]: () => json(409, { detail: text }) });
    renderSettings();
    await userEvent.type(await openConfirmation(), 'hemmelig1');

    await userEvent.click(screen.getByRole('button', { name: 'Ja, slett kontoen' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(text);
  });

  it('sends the password, signs out and goes to sign-in on success', async () => {
    // Guards setSession(null) after a successful deletion and the cache clear.
    const bodies: unknown[] = [];
    fakeApi({
      ...signedInWith(),
      [`POST ${PATH}`]: async (request) => {
        bodies.push(await request.json());
        return new Response(null, { status: 204 });
      },
    });
    renderSettings();
    await userEvent.type(await openConfirmation(), 'hemmelig1');

    await userEvent.click(screen.getByRole('button', { name: 'Ja, slett kontoen' }));

    expect(await screen.findByRole('heading', { name: /Logg inn/ })).toBeInTheDocument();
    expect(bodies).toEqual([{ password: 'hemmelig1' }]);
  });

  it('removes what this device kept for the user: the last Home and the browser subscription', async () => {
    // Guards forgetLastHome and unsubscribeThisBrowser after a successful deletion.
    const push = fakePush({ permission: 'granted', subscribed: true });
    fakeApi({ ...signedInWith(), [`POST ${PATH}`]: () => new Response(null, { status: 204 }) });
    localStorage.setItem(lastHomeKey(OLA.id), OLAS_HOME.id);
    renderSettings();
    await userEvent.type(await openConfirmation(), 'hemmelig1');

    await userEvent.click(screen.getByRole('button', { name: 'Ja, slett kontoen' }));

    await screen.findByRole('heading', { name: /Logg inn/ });
    expect(localStorage.getItem(lastHomeKey(OLA.id))).toBeNull();
    await waitFor(() => expect(push.unsubscribe).toHaveBeenCalledOnce());
  });

  it('closes the confirmation on «Avbryt», sends nothing and gives focus back', async () => {
    // Guards cancel(): the failed attempt is cleared and focus returns to the first button.
    const server = fakeApi({ ...signedInWith(), [`POST ${PATH}`]: () => json(204) });
    renderSettings();
    await openConfirmation();

    await userEvent.click(screen.getByRole('button', { name: 'Avbryt' }));

    const trigger = await screen.findByRole('button', { name: 'Slett konto' });
    await waitFor(() => expect(trigger).toHaveFocus());
    expect(server.calls('POST', PATH)).toHaveLength(0);
  });
});

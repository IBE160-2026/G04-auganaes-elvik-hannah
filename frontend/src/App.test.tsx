// Story 1.2 (FR-1): routes, forms and the session restored on load. Story 1.3: the landing page
// is the Home page, or Create Home for a user without a Home. Story 2.2: "/" opens the Home's
// Task Overview, and «Logg ut» is on Settings (and on Create Home).
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from './App';
import { MESSAGES } from './api/auth';
import { lastHomeKey } from './api/lastHome';
import { OLA, OLAS_HOME, authResponse, fakeApi, homesResponse, json, resetApi } from './test-utils/fakeApi';

const signedOut = { 'POST /api/auth/refresh': () => json(401, { detail: 'Økten er utløpt.' }) };
const withHome = { 'GET /api/homes': () => json(200, homesResponse()) };

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

afterEach(resetApi);

describe('App routes', () => {
  it('sends a signed-out visitor from / to /logg-inn', async () => {
    fakeApi(signedOut);
    renderAt('/');

    expect(await screen.findByRole('heading', { name: 'Logg inn' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/logg-inn');
  });

  it('restores the session from the refresh cookie on load (reload stays signed in)', async () => {
    const server = fakeApi({
      'POST /api/auth/refresh': () => json(200, authResponse('a1')),
      'GET /api/auth/me': () => json(200, OLA),
      ...withHome,
    });
    renderAt('/');

    expect(await screen.findByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();
    expect(server.calls('POST', '/api/auth/refresh')).toHaveLength(1);
  });

  it('signs in and shows the Home page with the name', async () => {
    fakeApi({
      ...signedOut,
      'POST /api/auth/login': () => json(200, authResponse('a1')),
      'GET /api/auth/me': () => json(200, OLA),
      ...withHome,
    });
    renderAt('/logg-inn');

    await userEvent.type(await screen.findByLabelText('E-post'), 'ola@example.com');
    await userEvent.type(screen.getByLabelText('Passord'), 'hemmelig1');
    await userEvent.click(screen.getByRole('button', { name: 'Logg inn' }));

    expect(await screen.findByRole('heading', { level: 1, name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}`);
    // AD-7: no token in storage. The only key is the most recently used Home (Story 2.2).
    await waitFor(() => expect(localStorage.getItem(lastHomeKey(OLA.id))).toBe(OLAS_HOME.id));
    expect(Object.keys(localStorage)).toEqual([lastHomeKey(OLA.id)]);
    expect(sessionStorage.length).toBe(0);
  });

  it('shows a wrong password inline, on the field, with focus there and no refresh', async () => {
    const server = fakeApi({
      ...signedOut,
      'POST /api/auth/login': () => json(401, { detail: 'Feil e-post eller passord.' }),
    });
    renderAt('/logg-inn');

    await userEvent.type(await screen.findByLabelText('E-post'), 'ola@example.com');
    await userEvent.type(screen.getByLabelText('Passord'), 'feilfeil1');
    await userEvent.click(screen.getByRole('button', { name: 'Logg inn' }));

    const password = screen.getByLabelText('Passord');
    await waitFor(() => expect(password).toHaveAttribute('aria-invalid', 'true'));
    expect(password).toHaveAccessibleDescription('Feil e-post eller passord.');
    await waitFor(() => expect(password).toHaveFocus());
    expect(window.location.pathname).toBe('/logg-inn');
    // Only the one refresh on load; the login 401 did not trigger another.
    expect(server.calls('POST', '/api/auth/refresh')).toHaveLength(1);
  });

  it('checks the register form before sending and focuses the first invalid field', async () => {
    const server = fakeApi(signedOut);
    renderAt('/registrer');

    await userEvent.type(await screen.findByLabelText('E-post'), 'ola@example.com');
    await userEvent.type(screen.getByLabelText('Passord'), 'kort');
    await userEvent.click(screen.getByRole('button', { name: 'Opprett konto' }));

    const name = screen.getByLabelText('Navn');
    await waitFor(() => expect(name).toHaveFocus());
    expect(name).toHaveAccessibleDescription(expect.stringContaining(MESSAGES.nameMissing));
    expect(screen.getByLabelText('Passord')).toHaveAccessibleDescription(
      expect.stringContaining(MESSAGES.passwordTooShort),
    );
    expect(server.calls('POST', '/api/auth/register')).toHaveLength(0);
  });

  it('offers "Logg inn i stedet" when the email already has an account', async () => {
    fakeApi({
      ...signedOut,
      'POST /api/auth/register': () =>
        json(409, { detail: 'Det finnes allerede en konto med denne e-posten.' }),
    });
    renderAt('/registrer');

    await userEvent.type(await screen.findByLabelText('E-post'), 'ola@example.com');
    await userEvent.type(screen.getByLabelText('Navn'), 'Ola');
    await userEvent.type(screen.getByLabelText('Passord'), 'hemmelig1');
    await userEvent.click(screen.getByRole('button', { name: 'Opprett konto' }));

    const link = await screen.findByRole('link', { name: 'Logg inn i stedet' });
    expect(screen.getByLabelText('E-post')).toHaveAttribute('aria-invalid', 'true');
    await userEvent.click(link);
    expect(await screen.findByRole('heading', { name: 'Logg inn' })).toBeInTheDocument();
  });

  it('shows server 422 errors on their fields', async () => {
    fakeApi({
      ...signedOut,
      'POST /api/auth/register': () =>
        json(422, { detail: [{ loc: ['body', 'email'], msg: 'x', type: 'value_error' }] }),
    });
    renderAt('/registrer');

    await userEvent.type(await screen.findByLabelText('E-post'), 'ola@example.c');
    await userEvent.type(screen.getByLabelText('Navn'), 'Ola');
    await userEvent.type(screen.getByLabelText('Passord'), 'hemmelig1');
    await userEvent.click(screen.getByRole('button', { name: 'Opprett konto' }));

    await waitFor(() =>
      expect(screen.getByLabelText('E-post')).toHaveAccessibleDescription(MESSAGES.emailInvalid),
    );
  });

  it('registers and, without a Home yet, lands on Create Home', async () => {
    fakeApi({
      ...signedOut,
      'POST /api/auth/register': () => json(201, authResponse('a1', { ...OLA, name: 'Mari' })),
      'GET /api/auth/me': () => json(200, { ...OLA, name: 'Mari' }),
      'GET /api/homes': () => json(200, homesResponse([], ['household', 'landlord'])),
    });
    renderAt('/registrer');

    await userEvent.type(await screen.findByLabelText('E-post'), 'mari@example.com');
    await userEvent.type(screen.getByLabelText('Navn'), 'Mari');
    await userEvent.type(screen.getByLabelText('Passord'), 'hemmelig1');
    await userEvent.click(screen.getByRole('button', { name: 'Opprett konto' }));

    expect(await screen.findByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/nytt-hjem');
  });

  it('signs out from Settings and returns to /logg-inn', async () => {
    const server = fakeApi({
      'POST /api/auth/refresh': () => json(200, authResponse('a1')),
      'GET /api/auth/me': () => json(200, OLA),
      ...withHome,
      'POST /api/auth/logout': () => new Response(null, { status: 204 }),
    });
    renderAt('/innstillinger');

    await userEvent.click(await screen.findByRole('button', { name: 'Logg ut' }));

    expect(await screen.findByRole('heading', { name: 'Logg inn' })).toBeInTheDocument();
    expect(server.calls('POST', '/api/auth/logout')).toHaveLength(1);
  });

  it('signs out in the frontend even when the logout request fails', async () => {
    fakeApi({
      'POST /api/auth/refresh': () => json(200, authResponse('a1')),
      'GET /api/auth/me': () => json(200, OLA),
      ...withHome,
      'POST /api/auth/logout': () => json(500, { detail: 'x' }),
    });
    renderAt('/innstillinger');

    await userEvent.click(await screen.findByRole('button', { name: 'Logg ut' }));

    expect(await screen.findByRole('heading', { name: 'Logg inn' })).toBeInTheDocument();
  });

  it('labels every input with autocomplete hints', async () => {
    fakeApi(signedOut);
    renderAt('/registrer');

    expect(await screen.findByLabelText('E-post')).toHaveAttribute('autocomplete', 'email');
    expect(screen.getByLabelText('Navn')).toHaveAttribute('autocomplete', 'name');
    expect(screen.getByLabelText('Passord')).toHaveAttribute('autocomplete', 'new-password');
  });
});

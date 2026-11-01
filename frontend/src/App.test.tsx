// Story 1.2 (FR-1): routes, forms and the session restored on load.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from './App';
import { MESSAGES } from './api/auth';
import { OLA, authResponse, fakeApi, json, resetApi } from './test-utils/fakeApi';

const signedOut = { 'POST /api/auth/refresh': () => json(401, { detail: 'Økten er utløpt.' }) };

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
    });
    renderAt('/');

    expect(await screen.findByText('Du er logget inn som Ola')).toBeInTheDocument();
    expect(server.calls('POST', '/api/auth/refresh')).toHaveLength(1);
  });

  it('signs in and shows the start page with the name', async () => {
    fakeApi({
      ...signedOut,
      'POST /api/auth/login': () => json(200, authResponse('a1')),
      'GET /api/auth/me': () => json(200, OLA),
    });
    renderAt('/logg-inn');

    await userEvent.type(await screen.findByLabelText('E-post'), 'ola@example.com');
    await userEvent.type(screen.getByLabelText('Passord'), 'hemmelig1');
    await userEvent.click(screen.getByRole('button', { name: 'Logg inn' }));

    expect(await screen.findByText('Du er logget inn som Ola')).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
    expect(localStorage.length + sessionStorage.length).toBe(0);
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

  it('registers and lands on the start page', async () => {
    fakeApi({
      ...signedOut,
      'POST /api/auth/register': () => json(201, authResponse('a1', { ...OLA, name: 'Mari' })),
      'GET /api/auth/me': () => json(200, { ...OLA, name: 'Mari' }),
    });
    renderAt('/registrer');

    await userEvent.type(await screen.findByLabelText('E-post'), 'mari@example.com');
    await userEvent.type(screen.getByLabelText('Navn'), 'Mari');
    await userEvent.type(screen.getByLabelText('Passord'), 'hemmelig1');
    await userEvent.click(screen.getByRole('button', { name: 'Opprett konto' }));

    expect(await screen.findByText('Du er logget inn som Mari')).toBeInTheDocument();
  });

  it('signs out and returns to /logg-inn', async () => {
    const server = fakeApi({
      'POST /api/auth/refresh': () => json(200, authResponse('a1')),
      'GET /api/auth/me': () => json(200, OLA),
      'POST /api/auth/logout': () => new Response(null, { status: 204 }),
    });
    renderAt('/');

    await userEvent.click(await screen.findByRole('button', { name: 'Logg ut' }));

    expect(await screen.findByRole('heading', { name: 'Logg inn' })).toBeInTheDocument();
    expect(server.calls('POST', '/api/auth/logout')).toHaveLength(1);
  });

  it('signs out in the frontend even when the logout request fails', async () => {
    fakeApi({
      'POST /api/auth/refresh': () => json(200, authResponse('a1')),
      'GET /api/auth/me': () => json(200, OLA),
      'POST /api/auth/logout': () => json(500, { detail: 'x' }),
    });
    renderAt('/');

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

// Story 1.4 (FR-2, UJ-1, UJ-2): every state of the invite page, and registering or signing in
// through a link without losing it.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import type { InvitePreview } from '../api/invites';
import { OLA, OLAS_HOME, authResponse, fakeApi, json, resetApi, signedInWith } from '../test-utils/fakeApi';

const TOKEN = 'tok_ABC-123';
const PREVIEW_PATH = `/api/invites/${TOKEN}`;
const ACCEPT_PATH = `/api/invites/${TOKEN}/accept`;

const VALID: InvitePreview = {
  status: 'valid',
  home_type: 'household',
  home_name: 'Kollektivet',
  role: 'household_member',
  viewer: null,
  other_home_name: null,
};

const signedOut = { 'POST /api/auth/refresh': () => json(401, { detail: 'Økten er utløpt.' }) };

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

async function fillRegister(email = 'jonas@example.com') {
  await userEvent.type(await screen.findByLabelText('E-post'), email);
  await userEvent.type(screen.getByLabelText('Navn'), 'Jonas');
  await userEvent.type(screen.getByLabelText('Passord'), 'hemmelig1');
  await userEvent.click(screen.getByRole('button', { name: 'Opprett konto' }));
}

async function fillSignIn() {
  await userEvent.type(await screen.findByLabelText('E-post'), 'ola@example.com');
  await userEvent.type(screen.getByLabelText('Passord'), 'hemmelig1');
  await userEvent.click(screen.getByRole('button', { name: 'Logg inn' }));
}

afterEach(resetApi);

describe('Invite page, signed out', () => {
  it('shows the Home and Role with "Opprett konto og bli med" and "Logg inn"', async () => {
    const server = fakeApi({ ...signedOut, [`GET ${PREVIEW_PATH}`]: () => json(200, VALID) });
    renderAt(`/invitasjon/${TOKEN}`);

    expect(await screen.findByRole('heading', { name: 'Bli med i «Kollektivet»' })).toBeInTheDocument();
    expect(screen.getByText(/som husstandsmedlem/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Opprett konto og bli med' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Logg inn' })).toHaveAttribute('href', `/logg-inn?invitasjon=${TOKEN}`);
    expect(server.calls('GET', PREVIEW_PATH)[0].headers.get('Authorization')).toBeNull();
  });

  it('registers through the link, joins in the same request and is told so', async () => {
    let joined = false;
    const server = fakeApi({
      ...signedOut,
      [`GET ${PREVIEW_PATH}`]: (request) =>
        json(200, request.headers.get('Authorization') && joined ? { ...VALID, viewer: 'already_member' } : VALID),
      'POST /api/auth/register': () => {
        joined = true;
        return json(201, { ...authResponse('a1', { ...OLA, name: 'Jonas' }), joined_home_id: OLAS_HOME.id });
      },
      'GET /api/auth/me': () => json(200, { ...OLA, name: 'Jonas' }),
      'GET /api/homes': () => json(200, { homes: [OLAS_HOME], allowed_types: [] }),
    });
    renderAt(`/invitasjon/${TOKEN}`);

    await userEvent.click(await screen.findByRole('button', { name: 'Opprett konto og bli med' }));
    expect(window.location.search).toBe(`?invitasjon=${TOKEN}`);
    await fillRegister();

    expect(await screen.findByText('Du er allerede med i «Kollektivet».')).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/invitasjon/${TOKEN}`);
    const [request] = server.calls('POST', '/api/auth/register');
    expect(await request.json()).toMatchObject({ email: 'jonas@example.com', invite_token: TOKEN });

    await userEvent.click(screen.getByRole('link', { name: 'Gå til forsiden' }));
    expect(await screen.findByRole('heading', { name: 'Kollektivet' })).toBeInTheDocument();
  });

  it('registers with a link that died meanwhile: the account exists, the page says the link is invalid', async () => {
    fakeApi({
      ...signedOut,
      [`GET ${PREVIEW_PATH}`]: () => json(200, { status: 'invalid', home_type: 'landlord' }),
      'POST /api/auth/register': () => json(201, { ...authResponse('a1'), joined_home_id: null }),
      'GET /api/auth/me': () => json(200, OLA),
    });
    renderAt(`/registrer?invitasjon=${TOKEN}`);

    await fillRegister();

    expect(
      await screen.findByText('Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra utleieren.'),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/invitasjon/${TOKEN}`);
  });

  it('offers "Logg inn i stedet" with the invite kept when the email is taken', async () => {
    fakeApi({
      ...signedOut,
      'POST /api/auth/register': () => json(409, { detail: 'Det finnes allerede en konto med denne e-posten.' }),
    });
    renderAt(`/registrer?invitasjon=${TOKEN}`);

    await fillRegister();

    expect(await screen.findByRole('link', { name: 'Logg inn i stedet' })).toHaveAttribute(
      'href',
      `/logg-inn?invitasjon=${TOKEN}`,
    );
  });

  it('keeps the invite in the links between sign-in and register', async () => {
    fakeApi(signedOut);
    renderAt(`/logg-inn?invitasjon=${TOKEN}`);

    await userEvent.click(await screen.findByRole('link', { name: 'Opprett konto' }));
    expect(window.location.search).toBe(`?invitasjon=${TOKEN}`);
    expect(await screen.findByRole('link', { name: 'Logg inn' })).toHaveAttribute('href', `/logg-inn?invitasjon=${TOKEN}`);
  });

  it('signs in through the link and returns to the invite page', async () => {
    fakeApi({
      ...signedOut,
      'POST /api/auth/login': () => json(200, authResponse('a1')),
      'GET /api/auth/me': () => json(200, OLA),
      [`GET ${PREVIEW_PATH}`]: (request) =>
        json(200, request.headers.get('Authorization') ? { ...VALID, viewer: 'can_join' } : VALID),
    });
    renderAt(`/logg-inn?invitasjon=${TOKEN}`);

    await fillSignIn();

    expect(await screen.findByRole('button', { name: 'Bli med i «Kollektivet»' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/invitasjon/${TOKEN}`);
  });

  it('ignores a malformed invitasjon value: links drop it and sign-in goes to "/"', async () => {
    fakeApi({
      ...signedOut,
      'POST /api/auth/login': () => json(200, authResponse('a1')),
      'GET /api/auth/me': () => json(200, OLA),
      'GET /api/homes': () => json(200, { homes: [OLAS_HOME], allowed_types: [] }),
    });
    renderAt('/logg-inn?invitasjon=..%2Fhjem%2Fx');

    expect(await screen.findByRole('link', { name: 'Opprett konto' })).toHaveAttribute('href', '/registrer');
    await fillSignIn();

    expect(await screen.findByRole('heading', { name: 'Kollektivet' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
  });

  it('falls back to the signed-out view when the session expired and refresh fails', async () => {
    let refreshes = 0;
    fakeApi({
      // Signed in on load; the next refresh (after the preview's 401) fails.
      'POST /api/auth/refresh': () => (refreshes++ === 0 ? json(200, authResponse('a1')) : json(401, { detail: 'x' })),
      'GET /api/auth/me': () => json(200, OLA),
      [`GET ${PREVIEW_PATH}`]: (request) =>
        request.headers.get('Authorization') ? json(401, { detail: 'Du må logge inn på nytt.' }) : json(200, VALID),
    });
    renderAt(`/invitasjon/${TOKEN}`);

    expect(await screen.findByRole('button', { name: 'Opprett konto og bli med' })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});

describe('Invite page, signed in', () => {
  it('joins with one tap and lands on the Home without bouncing', async () => {
    let accepted = false;
    const server = fakeApi({
      ...signedInWith([], ['household', 'landlord']),
      [`GET ${PREVIEW_PATH}`]: () => json(200, { ...VALID, viewer: 'can_join' }),
      // After the join, the Homes refetch never answers: only the cache write can show the Home.
      'GET /api/homes': () =>
        accepted ? new Promise<Response>(() => {}) : json(200, { homes: [], allowed_types: ['household', 'landlord'] }),
      [`POST ${ACCEPT_PATH}`]: () => {
        accepted = true;
        return json(200, OLAS_HOME);
      },
    });
    renderAt(`/invitasjon/${TOKEN}`);

    await userEvent.click(await screen.findByRole('button', { name: 'Bli med i «Kollektivet»' }));

    expect(await screen.findByRole('heading', { name: 'Kollektivet' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
    expect(server.calls('POST', ACCEPT_PATH)).toHaveLength(1);
  });

  it('tells a Member of the Home they are already in, with a link home', async () => {
    fakeApi({ ...signedInWith(), [`GET ${PREVIEW_PATH}`]: () => json(200, { ...VALID, viewer: 'already_member' }) });
    renderAt(`/invitasjon/${TOKEN}`);

    expect(await screen.findByText('Du er allerede med i «Kollektivet».')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Gå til forsiden' })).toHaveAttribute('href', '/');
    expect(screen.queryByRole('button', { name: /Bli med/ })).not.toBeInTheDocument();
  });

  it('tells a Member of another Home why they cannot join, without a join button', async () => {
    fakeApi({
      ...signedInWith(),
      [`GET ${PREVIEW_PATH}`]: () =>
        json(200, { ...VALID, home_name: 'Storgata 12', viewer: 'in_other_home', other_home_name: 'Kollektivet' }),
    });
    renderAt(`/invitasjon/${TOKEN}`);

    expect(
      await screen.findByText('Du er allerede med i «Kollektivet». Du kan bare være med i ett hjem om gangen.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Invitasjon til «Storgata 12»' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Bli med/ })).not.toBeInTheDocument();
  });

  it('shows the server reason when the link dies before the tap, then the invalid message', async () => {
    let gone = false;
    fakeApi({
      ...signedInWith([], ['household', 'landlord']),
      [`GET ${PREVIEW_PATH}`]: () =>
        json(200, gone ? { status: 'invalid', home_type: 'household' } : { ...VALID, viewer: 'can_join' }),
      [`POST ${ACCEPT_PATH}`]: () => {
        gone = true;
        return json(410, { detail: 'Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra et husstandsmedlem.' });
      },
    });
    renderAt(`/invitasjon/${TOKEN}`);

    await userEvent.click(await screen.findByRole('button', { name: 'Bli med i «Kollektivet»' }));

    expect(await screen.findByRole('heading', { name: 'Invitasjonen gjelder ikke lenger' })).toBeInTheDocument();
    expect(
      screen.getByText('Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra et husstandsmedlem.'),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/invitasjon/${TOKEN}`);
  });
});

describe('Invite page, invalid links', () => {
  it.each([
    ['landlord', 'utleieren'],
    ['household', 'et husstandsmedlem'],
    [null, 'den som inviterte deg'],
  ] as const)('an invalid %s link asks for a new one from %s, never a 404', async (homeType, whom) => {
    fakeApi({ ...signedOut, [`GET ${PREVIEW_PATH}`]: () => json(200, { status: 'invalid', home_type: homeType }) });
    renderAt(`/invitasjon/${TOKEN}`);

    expect(
      await screen.findByText(`Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra ${whom}.`),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/invitasjon/${TOKEN}`);
  });

  it('shows a malformed token as invalid without asking the server', async () => {
    const server = fakeApi(signedOut);
    renderAt('/invitasjon/ikke.gyldig');

    expect(
      await screen.findByText('Denne invitasjonslenken er ikke lenger gyldig — be om en ny fra den som inviterte deg.'),
    ).toBeInTheDocument();
    expect(server.requests.filter((r) => r.url.includes('/api/invites/'))).toHaveLength(0);
  });

  it('shows a failed load inline with a retry', async () => {
    let fail = true;
    fakeApi({
      ...signedOut,
      [`GET ${PREVIEW_PATH}`]: () => (fail ? json(500, { detail: 'x' }) : json(200, VALID)),
    });
    renderAt(`/invitasjon/${TOKEN}`);

    expect(await screen.findByRole('alert')).toHaveTextContent('Vi fikk ikke hentet invitasjonen.');
    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Bli med i «Kollektivet»' })).toBeInTheDocument());
  });
});

// Story 1.4 (FR-2, team decision 4): "Medlemmer og invitasjon". The invite control follows the
// server's can_invite; a Tenant never sees it.
// Story 1.5 (FR-3, SM-6): the members list on the same page, for every Role.
// Story 1.8 (FR-23): «Forlat hjemmet», «Fjern», their inline confirmation and the 403 redirect.
import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { HOME_MESSAGES, MEMBER_MESSAGES, type Home, type Member } from '../api/homes';
import {
  OLAS_HOME,
  fakeApi,
  homesResponse,
  json,
  membersPath,
  olaAs,
  resetApi,
  signedInWith,
} from '../test-utils/fakeApi';

const RENTAL: Home = {
  ...OLAS_HOME,
  id: '00000000-0000-4000-8000-0000000000b1',
  name: 'Storgata 12',
  type: 'landlord',
  role: 'landlord',
  can_leave: false,
};
const TENANCY: Home = { ...RENTAL, role: 'tenant', can_invite: false, can_leave: true };

const invitesPath = (home: Home) => `/api/homes/${home.id}/invites`;
const invite = (token: string) => ({ token, role: 'household_member', expires_at: '2026-11-14T12:00:00Z' });

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

afterEach(resetApi);

describe('Members & Invite page', () => {
  it('is linked from the Home page for the shown Home', async () => {
    fakeApi(signedInWith());
    renderAt('/');

    await userEvent.click(await screen.findByRole('link', { name: 'Medlemmer og invitasjon' }));

    expect(await screen.findByRole('heading', { name: 'Medlemmer og invitasjon' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}/medlemmer`);
  });

  it('links each of a Landlord\'s Homes to its own page', async () => {
    const second = { ...RENTAL, id: '00000000-0000-4000-8000-0000000000b2', name: 'Storgata 14' };
    fakeApi(signedInWith([second, RENTAL], ['landlord']));
    renderAt('/');

    expect(await screen.findByRole('link', { name: 'Medlemmer og invitasjon for Storgata 12' })).toHaveAttribute(
      'href',
      `/hjem/${RENTAL.id}/medlemmer`,
    );
    expect(screen.getByRole('link', { name: 'Medlemmer og invitasjon for Storgata 14' })).toHaveAttribute(
      'href',
      `/hjem/${second.id}/medlemmer`,
    );
  });

  it('lets a Household Member make a link, copy it and make another', async () => {
    const user = userEvent.setup();
    let n = 0;
    const server = fakeApi({
      ...signedInWith(),
      [`POST ${invitesPath(OLAS_HOME)}`]: () => json(201, invite(`token-${++n}`)),
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    expect(await screen.findByText('Kollektivet')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Lag invitasjonslenke' }));

    const field = await screen.findByLabelText('Invitasjonslenke');
    expect(field).toHaveValue(`${window.location.origin}/invitasjon/token-1`);
    expect(field).toHaveAttribute('readonly');
    expect(screen.getByText(/^Kan brukes én gang, gyldig til /)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Kopier lenke' }));
    expect(await screen.findByText('Lenken er kopiert.')).toBeInTheDocument();
    expect(await navigator.clipboard.readText()).toBe(`${window.location.origin}/invitasjon/token-1`);

    await user.click(screen.getByRole('button', { name: 'Lag ny lenke' }));
    await waitFor(() => expect(screen.getByLabelText('Invitasjonslenke')).toHaveValue(`${window.location.origin}/invitasjon/token-2`));
    expect(server.calls('POST', invitesPath(OLAS_HOME))).toHaveLength(2);
  });

  it('gives the Landlord the invite control too', async () => {
    fakeApi({
      ...signedInWith([RENTAL], ['landlord']),
      [`POST ${invitesPath(RENTAL)}`]: () => json(201, { ...invite('t1'), role: 'tenant' }),
    });
    renderAt(`/hjem/${RENTAL.id}/medlemmer`);

    expect(await screen.findByText(/send den til en ny leietaker/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Lag invitasjonslenke' }));
    expect(await screen.findByLabelText('Invitasjonslenke')).toHaveValue(`${window.location.origin}/invitasjon/t1`);
  });

  it('shows a Tenant no invite control at all, only who invites', async () => {
    fakeApi(signedInWith([TENANCY], []));
    renderAt(`/hjem/${TENANCY.id}/medlemmer`);

    expect(await screen.findByText('Det er utleieren som inviterer nye leietakere.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /lenke/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Inviter' })).not.toBeInTheDocument();
  });

  it('shows a failed generate inline at the button, and retries', async () => {
    let fail = true;
    fakeApi({
      ...signedInWith(),
      [`POST ${invitesPath(OLAS_HOME)}`]: () => (fail ? json(500, { detail: 'x' }) : json(201, invite('t1'))),
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    await userEvent.click(await screen.findByRole('button', { name: 'Lag invitasjonslenke' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Vi fikk ikke laget en invitasjonslenke.');

    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));
    expect(await screen.findByLabelText('Invitasjonslenke')).toHaveValue(`${window.location.origin}/invitasjon/t1`);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('waits while the Homes load and never redirects', async () => {
    const server = fakeApi({ ...signedInWith(), 'GET /api/homes': () => new Promise<Response>(() => {}) });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    await waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(1));
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(screen.getByRole('status')).toHaveTextContent('Laster …');
    expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}/medlemmer`);
  });

  it('shows a failed load inline with a retry, without redirecting', async () => {
    fakeApi({ ...signedInWith(), 'GET /api/homes': () => json(500, { detail: 'x' }) });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    expect(await screen.findByRole('alert')).toHaveTextContent(HOME_MESSAGES.loadFailed);
    expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}/medlemmer`);
  });

  it('sends a user to "/" when the loaded list does not have this Home', async () => {
    fakeApi(signedInWith());
    renderAt('/hjem/00000000-0000-4000-8000-0000000000ff/medlemmer');

    expect(await screen.findByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
  });
});

const KARI: Member = { user_id: '00000000-0000-4000-8000-000000000002', name: 'Kari', role: 'landlord', is_you: false, can_remove: false };
const JONAS: Member = {
  user_id: '00000000-0000-4000-8000-000000000003',
  name: 'Jonas',
  role: 'household_member',
  is_you: false,
  can_remove: false,
};

async function memberRows() {
  const section = await screen.findByRole('region', { name: 'Medlemmer' });
  const list = await within(section).findByRole('list');
  return within(list)
    .getAllByRole('listitem')
    .map((item) => item.firstElementChild?.textContent);
}

describe('Members list', () => {
  it('shows a Household Member every Member with their Role, and marks their own row', async () => {
    fakeApi({
      ...signedInWith(),
      [`GET ${membersPath(OLAS_HOME)}`]: () => json(200, { members: [olaAs('household_member'), JONAS] }),
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    expect(await screen.findByRole('heading', { name: 'Medlemmer' })).toBeInTheDocument();
    expect(await memberRows()).toEqual(['Ola (deg), Husstandsmedlem', 'Jonas, Husstandsmedlem']);
    expect(screen.getByRole('button', { name: 'Lag invitasjonslenke' })).toBeInTheDocument();
  });

  it('shows the Landlord herself first, then the Tenants', async () => {
    const anders: Member = { user_id: '00000000-0000-4000-8000-000000000004', name: 'Anders', role: 'tenant', is_you: false, can_remove: true };
    fakeApi({
      ...signedInWith([RENTAL], ['landlord']),
      [`GET ${membersPath(RENTAL)}`]: () => json(200, { members: [olaAs('landlord'), anders] }),
    });
    renderAt(`/hjem/${RENTAL.id}/medlemmer`);

    expect(await memberRows()).toEqual(['Ola (deg), Utleier', 'Anders, Leietaker']);
  });

  it('shows a Tenant the list but no invite control', async () => {
    fakeApi({
      ...signedInWith([TENANCY], []),
      [`GET ${membersPath(TENANCY)}`]: () => json(200, { members: [KARI, olaAs('tenant')] }),
    });
    renderAt(`/hjem/${TENANCY.id}/medlemmer`);

    expect(await memberRows()).toEqual(['Kari, Utleier', 'Ola (deg), Leietaker']);
    expect(screen.getByText('Det er utleieren som inviterer nye leietakere.')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Inviter' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /lenke/ })).not.toBeInTheDocument();
  });

  it('marks only the caller when two Members share a name', async () => {
    const otherOla: Member = { ...JONAS, name: 'Ola' };
    fakeApi({
      ...signedInWith(),
      [`GET ${membersPath(OLAS_HOME)}`]: () => json(200, { members: [otherOla, olaAs('household_member')] }),
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    expect(await memberRows()).toEqual(['Ola, Husstandsmedlem', 'Ola (deg), Husstandsmedlem']);
  });

  it('shows a single Member as one row marked "(deg)"', async () => {
    fakeApi(signedInWith());
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    expect(await memberRows()).toEqual(['Ola (deg), Husstandsmedlem']);
  });

  it('shows a failed members load at the list with a retry, and the invite control still works', async () => {
    const user = userEvent.setup();
    let fail = true;
    const server = fakeApi({
      ...signedInWith(),
      [`GET ${membersPath(OLAS_HOME)}`]: () =>
        fail ? json(500, { detail: 'x' }) : json(200, { members: [olaAs('household_member'), JONAS] }),
      [`POST ${invitesPath(OLAS_HOME)}`]: () => json(201, invite('t1')),
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    expect(await screen.findByRole('alert')).toHaveTextContent(MEMBER_MESSAGES.loadFailed);
    await user.click(screen.getByRole('button', { name: 'Lag invitasjonslenke' }));
    expect(await screen.findByLabelText('Invitasjonslenke')).toHaveValue(`${window.location.origin}/invitasjon/t1`);

    fail = false;
    await user.click(screen.getByRole('button', { name: 'Prøv å hente medlemmene igjen' }));
    expect(await memberRows()).toEqual(['Ola (deg), Husstandsmedlem', 'Jonas, Husstandsmedlem']);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(server.calls('GET', membersPath(OLAS_HOME))).toHaveLength(2);
  });

  it('shows its own loading text without a second status region', async () => {
    fakeApi({ ...signedInWith(), [`GET ${membersPath(OLAS_HOME)}`]: () => new Promise<Response>(() => {}) });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    expect(await screen.findByText('Henter medlemmer …')).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Lag invitasjonslenke' })).toBeInTheDocument();
  });

  it('never asks for the members of a Home that is not in the list', async () => {
    const foreign = { id: '00000000-0000-4000-8000-0000000000ff' };
    const server = fakeApi(signedInWith());
    renderAt(`/hjem/${foreign.id}/medlemmer`);

    expect(await screen.findByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();
    expect(server.calls('GET', membersPath(foreign))).toHaveLength(0);
  });
});

// Story 1.8 (FR-23): leave a Home and remove a Tenant, the frontend rows of the spec's matrix.
const ANDERS: Member = {
  user_id: '00000000-0000-4000-8000-000000000004',
  name: 'Anders',
  role: 'tenant',
  is_you: false,
  can_remove: true,
};
const leavePath = (home: Home) => `${membersPath(home)}/me`;
const removePath = (home: Home, member: Member) => `${membersPath(home)}/${member.user_id}`;
const noContent = () => new Response(null, { status: 204 });

describe('Leave and remove', () => {
  it('shows the Landlord «Fjern» on Tenants only, and no leave', async () => {
    fakeApi({
      ...signedInWith([RENTAL], ['landlord']),
      [`GET ${membersPath(RENTAL)}`]: () => json(200, { members: [olaAs('landlord'), ANDERS] }),
    });
    renderAt(`/hjem/${RENTAL.id}/medlemmer`);

    expect(await screen.findByRole('button', { name: 'Fjern Anders' })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /^Fjern/ })).toHaveLength(1);
    expect(screen.queryByRole('button', { name: 'Forlat hjemmet' })).not.toBeInTheDocument();
  });

  it.each([
    ['a Household Member', OLAS_HOME, [olaAs('household_member'), JONAS]],
    ['a Tenant', TENANCY, [KARI, olaAs('tenant')]],
  ] as const)('shows %s «Forlat hjemmet» and no «Fjern»', async (_, home, list) => {
    fakeApi({ ...signedInWith([home]), [`GET ${membersPath(home)}`]: () => json(200, { members: list }) });
    renderAt(`/hjem/${home.id}/medlemmer`);

    expect(await screen.findByRole('button', { name: 'Forlat hjemmet' })).toBeInTheDocument();
    await memberRows();
    expect(screen.queryByRole('button', { name: /^Fjern/ })).not.toBeInTheDocument();
  });

  it('confirms inline before leaving, and «Avbryt» sends nothing and returns focus', async () => {
    const user = userEvent.setup();
    const server = fakeApi({ ...signedInWith(), [`DELETE ${leavePath(OLAS_HOME)}`]: noContent });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Forlat hjemmet' }));

    expect(screen.getByText('Du mister tilgangen til «Kollektivet». Oppgavene du har gjort, blir stående.')).toBeInTheDocument();
    const confirm = screen.getByRole('button', { name: 'Ja, forlat hjemmet' });
    expect(document.activeElement).toBe(confirm);
    expect(confirm).toHaveAccessibleDescription(/Du mister tilgangen/);

    await user.click(screen.getByRole('button', { name: 'Avbryt' }));

    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Forlat hjemmet' }));
    expect(screen.queryByRole('button', { name: 'Ja, forlat hjemmet' })).not.toBeInTheDocument();
    expect(server.calls('DELETE', leavePath(OLAS_HOME))).toHaveLength(0);
  });

  it('after leaving, lands on Create Home with the notice, which survives both redirects', async () => {
    const user = userEvent.setup();
    let left = false;
    const server = fakeApi({
      ...signedInWith(),
      'GET /api/homes': () =>
        json(200, left ? homesResponse([], ['household', 'landlord']) : homesResponse([OLAS_HOME])),
      [`DELETE ${leavePath(OLAS_HOME)}`]: () => {
        left = true;
        return noContent();
      },
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Forlat hjemmet' }));
    await user.click(screen.getByRole('button', { name: 'Ja, forlat hjemmet' }));

    const notice = await screen.findByText('Du har forlatt «Kollektivet».');
    expect(notice).toHaveAttribute('aria-live', 'polite');
    expect(notice).not.toHaveAttribute('role');
    expect(window.location.pathname).toBe('/nytt-hjem');
    expect(screen.getByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(server.calls('DELETE', leavePath(OLAS_HOME))).toHaveLength(1);
  });

  it('sends a Landlord who leaves a Household to "/" with the notice, keeping her Landlord Home', async () => {
    const user = userEvent.setup();
    let left = false;
    fakeApi({
      ...signedInWith([OLAS_HOME, RENTAL], ['landlord']),
      'GET /api/homes': () =>
        json(200, homesResponse(left ? [RENTAL] : [OLAS_HOME, RENTAL], ['landlord'])),
      [`DELETE ${leavePath(OLAS_HOME)}`]: () => {
        left = true;
        return noContent();
      },
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Forlat hjemmet' }));
    await user.click(screen.getByRole('button', { name: 'Ja, forlat hjemmet' }));

    expect(await screen.findByText('Du har forlatt «Kollektivet».')).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
    expect(screen.getByRole('heading', { name: 'Storgata 12' })).toBeInTheDocument();
  });

  it('shows a failed leave inline with «Prøv igjen», keeps focus, and retries', async () => {
    const user = userEvent.setup();
    let fail = true;
    fakeApi({
      ...signedInWith(),
      [`DELETE ${leavePath(OLAS_HOME)}`]: () => (fail ? json(500, { detail: 'x' }) : noContent()),
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Forlat hjemmet' }));
    await user.click(screen.getByRole('button', { name: 'Ja, forlat hjemmet' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(MEMBER_MESSAGES.leaveFailed);
    const retry = screen.getByRole('button', { name: 'Prøv igjen' });
    expect(document.activeElement).toBe(retry);
    expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}/medlemmer`);

    fail = false;
    await user.click(retry);
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  });

  it('shows no inline error when the leave is refused (403), and refetches the Homes', async () => {
    const user = userEvent.setup();
    let removed = false;
    const server = fakeApi({
      ...signedInWith([TENANCY]),
      'GET /api/homes': () =>
        json(200, removed ? homesResponse([], ['household', 'landlord']) : homesResponse([TENANCY])),
      [`DELETE ${leavePath(TENANCY)}`]: () => {
        removed = true;
        return json(403, { detail: 'Du har ikke tilgang til dette i dette hjemmet.' });
      },
    });
    renderAt(`/hjem/${TENANCY.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Forlat hjemmet' }));
    await user.click(screen.getByRole('button', { name: 'Ja, forlat hjemmet' }));

    await waitFor(() => expect(window.location.pathname).toBe('/nytt-hjem'));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(server.calls('GET', '/api/homes').length).toBeGreaterThanOrEqual(2);
  });

  it('lets the Landlord remove a Tenant: confirm, notice, and focus on the heading', async () => {
    const user = userEvent.setup();
    let removed = false;
    const server = fakeApi({
      ...signedInWith([RENTAL], ['landlord']),
      [`GET ${membersPath(RENTAL)}`]: () =>
        json(200, { members: removed ? [olaAs('landlord')] : [olaAs('landlord'), ANDERS] }),
      [`DELETE ${removePath(RENTAL, ANDERS)}`]: () => {
        removed = true;
        return noContent();
      },
    });
    renderAt(`/hjem/${RENTAL.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Fjern Anders' }));
    expect(screen.getByText('Anders mister tilgangen til «Storgata 12».')).toBeInTheDocument();
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Ja, fjern Anders' }));
    expect(server.calls('DELETE', removePath(RENTAL, ANDERS))).toHaveLength(0);

    await user.click(screen.getByRole('button', { name: 'Ja, fjern Anders' }));

    const notice = await screen.findByText('Anders er fjernet.');
    expect(notice).toHaveAttribute('aria-live', 'polite');
    expect(await memberRows()).toEqual(['Ola (deg), Utleier']);
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Medlemmer' }));
    expect(server.calls('DELETE', removePath(RENTAL, ANDERS))).toHaveLength(1);
  });

  it('«Avbryt» on remove sends nothing and returns focus to «Fjern»', async () => {
    const user = userEvent.setup();
    const server = fakeApi({
      ...signedInWith([RENTAL], ['landlord']),
      [`GET ${membersPath(RENTAL)}`]: () => json(200, { members: [olaAs('landlord'), ANDERS] }),
    });
    renderAt(`/hjem/${RENTAL.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Fjern Anders' }));
    await user.click(screen.getByRole('button', { name: 'Avbryt' }));

    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Fjern Anders' }));
    expect(server.calls('DELETE', removePath(RENTAL, ANDERS))).toHaveLength(0);
  });

  it('shows a failed remove inline with «Prøv igjen», keeping focus and the row', async () => {
    const user = userEvent.setup();
    fakeApi({
      ...signedInWith([RENTAL], ['landlord']),
      [`GET ${membersPath(RENTAL)}`]: () => json(200, { members: [olaAs('landlord'), ANDERS] }),
      [`DELETE ${removePath(RENTAL, ANDERS)}`]: () => json(500, { detail: 'x' }),
    });
    renderAt(`/hjem/${RENTAL.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Fjern Anders' }));
    await user.click(screen.getByRole('button', { name: 'Ja, fjern Anders' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(MEMBER_MESSAGES.removeFailed);
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Prøv igjen' }));
    expect(await memberRows()).toEqual(['Ola (deg), Utleier', 'Anders, Leietaker']);
  });

  it('refreshes the list without an error when the Tenant already left (403)', async () => {
    const user = userEvent.setup();
    let gone = false;
    // The refetch after the 403 is held back, so the folded confirmation can be checked first.
    let releaseRefetch = () => {};
    const refetched = new Promise<void>((resolve) => (releaseRefetch = resolve));
    const server = fakeApi({
      ...signedInWith([RENTAL], ['landlord']),
      [`GET ${membersPath(RENTAL)}`]: async () => {
        if (!gone) return json(200, { members: [olaAs('landlord'), ANDERS] });
        await refetched;
        return json(200, { members: [olaAs('landlord')] });
      },
      [`DELETE ${removePath(RENTAL, ANDERS)}`]: () => {
        gone = true;
        return json(403, { detail: 'Du har ikke tilgang til dette i dette hjemmet.' });
      },
    });
    renderAt(`/hjem/${RENTAL.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Fjern Anders' }));
    await user.click(screen.getByRole('button', { name: 'Ja, fjern Anders' }));

    // Folded back to «Fjern»: no second DELETE can be sent during the refetch.
    expect(await screen.findByRole('button', { name: 'Fjern Anders' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Ja, fjern Anders' })).not.toBeInTheDocument();
    expect(server.calls('DELETE', removePath(RENTAL, ANDERS))).toHaveLength(1);

    releaseRefetch();
    await waitFor(async () => expect(await memberRows()).toEqual(['Ola (deg), Utleier']));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByText('Anders er fjernet.')).not.toBeInTheDocument();
    expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Medlemmer' }));
    expect(server.calls('GET', membersPath(RENTAL))).toHaveLength(2);
  });

  it('keeps one Tenant\'s pending remove when another row is cancelled', async () => {
    const user = userEvent.setup();
    const per: Member = { ...ANDERS, user_id: '00000000-0000-4000-8000-000000000005', name: 'Per' };
    let removed = false;
    let finishDelete = () => {};
    const deleted = new Promise<void>((resolve) => (finishDelete = resolve));
    const server = fakeApi({
      ...signedInWith([RENTAL], ['landlord']),
      [`GET ${membersPath(RENTAL)}`]: () =>
        json(200, { members: removed ? [olaAs('landlord'), per] : [olaAs('landlord'), ANDERS, per] }),
      [`DELETE ${removePath(RENTAL, ANDERS)}`]: async () => {
        await deleted;
        removed = true;
        return noContent();
      },
    });
    renderAt(`/hjem/${RENTAL.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Fjern Anders' }));
    await user.click(screen.getByRole('button', { name: 'Ja, fjern Anders' }));
    await waitFor(() => expect(server.calls('DELETE', removePath(RENTAL, ANDERS))).toHaveLength(1));
    const perRow = screen.getByRole('button', { name: 'Fjern Per' }).closest('li') as HTMLElement;
    await user.click(within(perRow).getByRole('button', { name: 'Fjern Per' }));
    await user.click(within(perRow).getByRole('button', { name: 'Avbryt' }));

    finishDelete();

    expect(await screen.findByText('Anders er fjernet.')).toBeInTheDocument();
    expect(await memberRows()).toEqual(['Ola (deg), Utleier', 'Per, Leietaker']);
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'Medlemmer' })));
    expect(server.calls('DELETE', removePath(RENTAL, per))).toHaveLength(0);
  });

  it('sends one DELETE when the confirm button is pressed twice while sending', async () => {
    const user = userEvent.setup();
    const server = fakeApi({
      ...signedInWith(),
      [`DELETE ${leavePath(OLAS_HOME)}`]: () => new Promise<Response>(() => {}),
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);

    await user.click(await screen.findByRole('button', { name: 'Forlat hjemmet' }));
    const confirm = screen.getByRole('button', { name: 'Ja, forlat hjemmet' });
    await user.click(confirm);
    await waitFor(() => expect(confirm).toHaveTextContent('Sender…'));
    await user.click(confirm);

    expect(confirm).toHaveAttribute('aria-busy', 'true');
    expect(confirm).toHaveAttribute('aria-disabled', 'true');
    expect(document.activeElement).toBe(confirm);
    expect(server.calls('DELETE', leavePath(OLAS_HOME))).toHaveLength(1);
  });

  it('shows the leave notice only once: not after navigating away and back', async () => {
    const user = userEvent.setup();
    let left = false;
    fakeApi({
      ...signedInWith(),
      'GET /api/homes': () =>
        json(200, left ? homesResponse([], ['household', 'landlord']) : homesResponse([OLAS_HOME])),
      [`DELETE ${leavePath(OLAS_HOME)}`]: () => {
        left = true;
        return noContent();
      },
    });
    renderAt(`/hjem/${OLAS_HOME.id}/medlemmer`);
    await user.click(await screen.findByRole('button', { name: 'Forlat hjemmet' }));
    await user.click(screen.getByRole('button', { name: 'Ja, forlat hjemmet' }));
    expect(await screen.findByText('Du har forlatt «Kollektivet».')).toBeInTheDocument();

    // Away to "/" (which sends a user without Homes back to Create Home), in the same app.
    act(() => {
      window.history.pushState({}, '', '/');
      window.dispatchEvent(new PopStateEvent('popstate'));
    });

    await waitFor(() => expect(window.location.pathname).toBe('/nytt-hjem'));
    expect(await screen.findByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.queryByText('Du har forlatt «Kollektivet».')).not.toBeInTheDocument();
  });

  it('sends a Tenant removed while signed in to Create Home on the next refetch, without a loop', async () => {
    let removed = false;
    let homesAfterRemoval = false;
    const server = fakeApi({
      ...signedInWith([TENANCY]),
      'GET /api/homes': () =>
        json(200, homesAfterRemoval ? homesResponse([], ['household', 'landlord']) : homesResponse([TENANCY])),
      [`GET ${membersPath(TENANCY)}`]: () => {
        if (!removed) return json(200, { members: [KARI, olaAs('tenant')] });
        // Only the refetch the 403 handler triggers sees the Homes without this one.
        homesAfterRemoval = true;
        return json(403, { detail: 'Du har ikke tilgang til dette i dette hjemmet.' });
      },
    });
    renderAt(`/hjem/${TENANCY.id}/medlemmer`);
    expect(await memberRows()).toEqual(['Kari, Utleier', 'Ola (deg), Leietaker']);

    removed = true;
    // Back to the tab: TanStack Query refetches on visibilitychange, no reload.
    window.dispatchEvent(new Event('visibilitychange'));

    await waitFor(() => expect(window.location.pathname).toBe('/nytt-hjem'));
    expect(await screen.findByRole('heading', { name: 'Opprett hjemmet ditt' })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(server.calls('GET', membersPath(TENANCY))).toHaveLength(2);
  });
});

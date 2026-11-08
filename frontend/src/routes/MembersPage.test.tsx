// Story 1.4 (FR-2, team decision 4): "Medlemmer og invitasjon". The invite control follows the
// server's can_invite; a Tenant never sees it.
// Story 1.5 (FR-3, SM-6): the members list on the same page, for every Role.
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { HOME_MESSAGES, MEMBER_MESSAGES, type Home, type Member } from '../api/homes';
import { OLAS_HOME, fakeApi, json, membersPath, olaAs, resetApi, signedInWith } from '../test-utils/fakeApi';

const RENTAL: Home = {
  ...OLAS_HOME,
  id: '00000000-0000-4000-8000-0000000000b1',
  name: 'Storgata 12',
  type: 'landlord',
  role: 'landlord',
};
const TENANCY: Home = { ...RENTAL, role: 'tenant', can_invite: false };

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

const KARI: Member = { user_id: '00000000-0000-4000-8000-000000000002', name: 'Kari', role: 'landlord', is_you: false };
const JONAS: Member = {
  user_id: '00000000-0000-4000-8000-000000000003',
  name: 'Jonas',
  role: 'household_member',
  is_you: false,
};

async function memberRows() {
  const section = await screen.findByRole('region', { name: 'Medlemmer' });
  const list = await within(section).findByRole('list');
  return within(list)
    .getAllByRole('listitem')
    .map((item) => item.textContent);
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
    const anders: Member = { user_id: '00000000-0000-4000-8000-000000000004', name: 'Anders', role: 'tenant', is_you: false };
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

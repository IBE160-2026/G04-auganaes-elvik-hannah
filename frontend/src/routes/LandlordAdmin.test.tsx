// Story 3.4 (FR-12, UX-DR12): Landlord Home Admin shell and its broadcast composer.
// The composer follows the server's can_broadcast; a count confirms in a polite live region and
// names nobody; a failed send keeps the text and offers «Prøv igjen».
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { BROADCAST_MAX, sentNotice } from '../api/broadcast';
import type { Home } from '../api/homes';
import { OLAS_HOME, fakeApi, json, resetApi, signedInWith } from '../test-utils/fakeApi';

const LANDLORD: Home = {
  ...OLAS_HOME,
  id: '00000000-0000-4000-8000-0000000000b1',
  name: 'Storgata 12',
  type: 'landlord',
  role: 'landlord',
  can_leave: false,
  can_broadcast: true,
};
const TENANCY: Home = { ...LANDLORD, role: 'tenant', can_invite: false, can_broadcast: false };

const path = (home: Home) => `/api/homes/${home.id}/broadcast`;

function renderAt(url: string) {
  window.history.pushState({}, '', url);
  return render(<App />);
}

afterEach(resetApi);

describe('Landlord Home Admin', () => {
  it('is linked from the Landlord\'s Task Overview and not from a household\'s', async () => {
    fakeApi(signedInWith([LANDLORD]));
    renderAt('/');
    await userEvent.click(await screen.findByRole('link', { name: 'Send melding til leietakerne' }));
    expect(await screen.findByRole('heading', { name: 'Administrer hjemmet' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${LANDLORD.id}/utleier`);
    resetApi();

    fakeApi(signedInWith([OLAS_HOME]));
    renderAt('/');
    await screen.findByRole('link', { name: 'Medlemmer og invitasjon' });
    expect(screen.queryByRole('link', { name: 'Send melding til leietakerne' })).toBeNull();
  });

  it('sends a Tenant who opens the page back to the Home', async () => {
    fakeApi(signedInWith([TENANCY]));
    renderAt(`/hjem/${TENANCY.id}/utleier`);

    expect(await screen.findByRole('heading', { level: 1, name: TENANCY.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${TENANCY.id}`);
  });

  it('sends the trimmed text, confirms with the count and clears the field', async () => {
    const api = fakeApi({
      ...signedInWith([LANDLORD]),
      [`POST ${path(LANDLORD)}`]: () => json(200, { recipients: 2, without_push: 1 }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);

    const field = await screen.findByLabelText('Melding');
    await userEvent.type(field, '  Rørlegger kommer i morgen.  ');
    await userEvent.click(screen.getByRole('button', { name: 'Send melding' }));

    const notice = await screen.findByText('Sendt til 2 leietakere. 1 kunne ikke nås med varsel.');
    expect(notice).toHaveAttribute('aria-live', 'polite');
    expect(field).toHaveValue('');
    const [request] = api.calls('POST', path(LANDLORD));
    expect(await request.json()).toEqual({ message: 'Rørlegger kommer i morgen.' });
  });

  it('refuses an empty or too long text without calling the server', async () => {
    const api = fakeApi(signedInWith([LANDLORD]));
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    const field = await screen.findByLabelText('Melding');

    await userEvent.click(screen.getByRole('button', { name: 'Send melding' }));
    expect(await screen.findByText('Skriv en melding først.')).toBeInTheDocument();
    expect(field).toHaveAttribute('aria-invalid', 'true');

    await userEvent.click(field);
    await userEvent.paste('x'.repeat(BROADCAST_MAX + 1));
    await userEvent.click(screen.getByRole('button', { name: 'Send melding' }));
    expect(await screen.findByText(`Meldingen kan ha maks ${BROADCAST_MAX} tegn.`)).toBeInTheDocument();
    expect(api.calls('POST', path(LANDLORD))).toHaveLength(0);
  });

  it('keeps the text after a failed send and retries with «Prøv igjen»', async () => {
    let attempts = 0;
    const api = fakeApi({
      ...signedInWith([LANDLORD]),
      [`POST ${path(LANDLORD)}`]: () =>
        ++attempts === 1 ? json(500, { detail: 'boom' }) : json(200, { recipients: 1, without_push: 0 }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    const field = await screen.findByLabelText('Melding');
    await userEvent.type(field, 'Hei alle');
    await userEvent.click(screen.getByRole('button', { name: 'Send melding' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Vi fikk ikke sendt meldingen.');
    expect(field).toHaveValue('Hei alle');

    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));

    // The retry confirms exactly as a first send does: notice shown and the field cleared.
    expect(await screen.findByText('Sendt til 1 leietaker.')).toHaveAttribute('aria-live', 'polite');
    expect(field).toHaveValue('');
    expect(api.calls('POST', path(LANDLORD))).toHaveLength(2);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('shows the server\'s reason for a Home without Tenants and offers no retry', async () => {
    fakeApi({
      ...signedInWith([LANDLORD]),
      [`POST ${path(LANDLORD)}`]: () => json(409, { detail: 'Det er ingen leietakere i hjemmet ennå.' }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    await userEvent.type(await screen.findByLabelText('Melding'), 'Hei');
    await userEvent.click(screen.getByRole('button', { name: 'Send melding' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Det er ingen leietakere i hjemmet ennå.');
    expect(screen.queryByRole('button', { name: 'Prøv igjen' })).toBeNull();
  });

  it('keeps the text when nobody was reached, and says so', async () => {
    fakeApi({
      ...signedInWith([LANDLORD]),
      [`POST ${path(LANDLORD)}`]: () => json(200, { recipients: 0, without_push: 2 }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    const field = await screen.findByLabelText('Melding');
    await userEvent.type(field, 'Hei alle');
    await userEvent.click(screen.getByRole('button', { name: 'Send melding' }));

    expect(await screen.findByText(/Ingen leietakere kunne nås/)).toBeInTheDocument();
    // Guards `if (result.recipients > 0) setText('')`.
    expect(field).toHaveValue('Hei alle');
  });

  it('checks the text again on «Prøv igjen» instead of sending an edited, invalid one', async () => {
    const api = fakeApi({
      ...signedInWith([LANDLORD]),
      [`POST ${path(LANDLORD)}`]: () => json(500, { detail: 'boom' }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    const field = await screen.findByLabelText('Melding');
    await userEvent.type(field, 'Hei');
    await userEvent.click(screen.getByRole('button', { name: 'Send melding' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Prøv igjen' }));
    expect(api.calls('POST', path(LANDLORD))).toHaveLength(2);

    await userEvent.clear(field);
    // The text is empty now: a retry must be refused by the same check as a first send.
    await userEvent.click(screen.getByRole('button', { name: 'Send melding' }));
    expect(await screen.findByText('Skriv en melding først.')).toBeInTheDocument();
    expect(api.calls('POST', path(LANDLORD))).toHaveLength(2);
  });

  it('shows no inline error for a 403: the Homes are refetched instead', async () => {
    const api = fakeApi({
      ...signedInWith([LANDLORD]),
      [`POST ${path(LANDLORD)}`]: () => json(403, { detail: 'Du har ikke tilgang til dette i dette hjemmet.' }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    await userEvent.type(await screen.findByLabelText('Melding'), 'Hei');
    const homesBefore = api.calls('GET', '/api/homes').length;
    await userEvent.click(screen.getByRole('button', { name: 'Send melding' }));

    // The refetch is what proves the 403 was handled before the no-alert check below.
    await waitFor(() => expect(api.calls('GET', '/api/homes').length).toBeGreaterThan(homesBefore));
    await waitFor(() => expect(api.calls('POST', path(LANDLORD))).toHaveLength(1));
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Prøv igjen' })).toBeNull();
  });
});

describe('sentNotice', () => {
  it('names nobody, says one Tenant in the singular and adds who has no push', () => {
    expect(sentNotice({ recipients: 1, without_push: 0 })).toBe('Sendt til 1 leietaker.');
    expect(sentNotice({ recipients: 3, without_push: 0 })).toBe('Sendt til 3 leietakere.');
    expect(sentNotice({ recipients: 2, without_push: 2 })).toBe(
      'Sendt til 2 leietakere. 2 kunne ikke nås med varsel.',
    );
    expect(sentNotice({ recipients: 0, without_push: 2 })).toContain('Ingen leietakere kunne nås');
  });
});

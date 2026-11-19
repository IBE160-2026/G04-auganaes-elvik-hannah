// Story 3.4 (FR-12, UX-DR12): Landlord Home Admin shell and its broadcast composer.
// Story 3.5 (FR-13, UX-DR30): the reminder cadence section on the same page.
// Story 4.1 (FR-18, AD-6): the «Bildebevis» section: one checkbox per task the server says may
// require a photo.
// The composer follows the server's can_broadcast; a count confirms in a polite live region and
// names nobody; a failed send keeps the text and offers «Prøv igjen».
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { BROADCAST_MAX, sentNotice } from '../api/broadcast';
import type { Home } from '../api/homes';
import {
  OLAS_HOME,
  OLAS_TASKS,
  fakeApi,
  json,
  resetApi,
  signedInWith,
  tasksPath,
} from '../test-utils/fakeApi';

const LANDLORD: Home = {
  ...OLAS_HOME,
  id: '00000000-0000-4000-8000-0000000000b1',
  name: 'Storgata 12',
  type: 'landlord',
  role: 'landlord',
  can_leave: false,
  can_broadcast: true,
  can_set_cadence: true,
  can_require_photo_evidence: true,
};
const TENANCY: Home = { ...LANDLORD, role: 'tenant', can_invite: false, can_broadcast: false };

const path = (home: Home) => `/api/homes/${home.id}/broadcast`;
const cadencePath = (home: Home) => `/api/homes/${home.id}/notification-cadence`;
const requirementPath = (home: Home, taskId: string) =>
  `/api/homes/${home.id}/tasks/${taskId}/photo-evidence-requirement`;
const SLUKET = OLAS_TASKS[0];

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

describe('Reminder cadence', () => {
  it('shows the saved cadence, saves another and confirms in a polite live region', async () => {
    let saved = 1;
    const api = fakeApi({
      ...signedInWith([LANDLORD]),
      'GET /api/homes': () =>
        json(200, {
          homes: [{ ...LANDLORD, notification_cadence_days: saved }],
          allowed_types: [],
          lived_in_home_id: null,
        }),
      [`PUT ${cadencePath(LANDLORD)}`]: async (request) => {
        saved = ((await request.json()) as { days: number }).days;
        return json(200, { notification_cadence_days: saved });
      },
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);

    expect(await screen.findByRole('radio', { name: 'Hver dag' })).toBeChecked();
    await userEvent.click(screen.getByRole('radio', { name: 'Én gang i uken' }));
    await userEvent.click(screen.getByRole('button', { name: 'Lagre' }));

    expect(await screen.findByText('Lagret.')).toHaveAttribute('aria-live', 'polite');
    const [request] = api.calls('PUT', cadencePath(LANDLORD));
    expect(await request.json()).toEqual({ days: 7 });
    // The Homes are fetched again, so the saved value is what the server now says.
    await waitFor(() => expect(screen.getByRole('radio', { name: 'Én gang i uken' })).toBeChecked());
  });

  it('offers only whole-day options', async () => {
    fakeApi(signedInWith([LANDLORD]));
    renderAt(`/hjem/${LANDLORD.id}/utleier`);

    await screen.findByRole('radio', { name: 'Hver dag' });
    expect(screen.getAllByRole('radio').map((r) => r.getAttribute('value'))).toEqual(['1', '2', '7']);
  });

  it('keeps the choice after a failed save and retries with «Prøv igjen»', async () => {
    let attempts = 0;
    const api = fakeApi({
      ...signedInWith([LANDLORD]),
      [`PUT ${cadencePath(LANDLORD)}`]: () =>
        ++attempts === 1 ? json(500, { detail: 'boom' }) : json(200, { notification_cadence_days: 2 }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    await userEvent.click(await screen.findByRole('radio', { name: 'Annenhver dag' }));
    await userEvent.click(screen.getByRole('button', { name: 'Lagre' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Vi fikk ikke lagret påminnelsene.');
    expect(screen.getByRole('radio', { name: 'Annenhver dag' })).toBeChecked();

    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));

    expect(await screen.findByText('Lagret.')).toBeInTheDocument();
    expect(api.calls('PUT', cadencePath(LANDLORD))).toHaveLength(2);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('drops the old error when another option is chosen', async () => {
    fakeApi({
      ...signedInWith([LANDLORD]),
      [`PUT ${cadencePath(LANDLORD)}`]: () => json(500, { detail: 'boom' }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    await userEvent.click(await screen.findByRole('radio', { name: 'Annenhver dag' }));
    await userEvent.click(screen.getByRole('button', { name: 'Lagre' }));
    await screen.findByRole('alert');

    await userEvent.click(screen.getByRole('radio', { name: 'Én gang i uken' }));

    // Guards `save.reset()` in the radio's onChange.
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('shows no inline error for a 403: the Homes are refetched instead', async () => {
    const api = fakeApi({
      ...signedInWith([LANDLORD]),
      [`PUT ${cadencePath(LANDLORD)}`]: () => json(403, { detail: 'Du har ikke tilgang.' }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    await userEvent.click(await screen.findByRole('radio', { name: 'Annenhver dag' }));
    const homesBefore = api.calls('GET', '/api/homes').length;
    await userEvent.click(screen.getByRole('button', { name: 'Lagre' }));

    await waitFor(() => expect(api.calls('GET', '/api/homes').length).toBeGreaterThan(homesBefore));
    expect(api.calls('PUT', cadencePath(LANDLORD))).toHaveLength(1);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('is not shown when the server does not allow the caller to set it', async () => {
    fakeApi(signedInWith([{ ...LANDLORD, can_set_cadence: false }]));
    renderAt(`/hjem/${LANDLORD.id}/utleier`);

    await screen.findByLabelText('Melding');
    expect(screen.queryByRole('radio')).toBeNull();
  });
});

describe('Photo Evidence', () => {
  it('lists only the tasks the server says may require a photo', async () => {
    fakeApi(signedInWith([LANDLORD]));
    renderAt(`/hjem/${LANDLORD.id}/utleier`);

    expect(await screen.findByRole('checkbox', { name: 'Krev bilde på «Rens sluket»' })).not.toBeChecked();
    // Guards the filter on may_require_photo_evidence: the other tasks get no checkbox.
    expect(screen.getAllByRole('checkbox')).toHaveLength(1);
  });

  it('saves the requirement for that task and shows what the server holds afterwards', async () => {
    let required = false;
    const api = fakeApi({
      ...signedInWith([LANDLORD]),
      [`GET ${tasksPath(LANDLORD)}`]: () =>
        json(200, { tasks: OLAS_TASKS.map((t) => ({ ...t, requires_photo_evidence: t === SLUKET && required })) }),
      [`PUT ${requirementPath(LANDLORD, SLUKET.id)}`]: async (request) => {
        required = ((await request.json()) as { required: boolean }).required;
        return json(200, { requires_photo_evidence: required });
      },
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);

    await userEvent.click(await screen.findByRole('checkbox', { name: 'Krev bilde på «Rens sluket»' }));

    await waitFor(() => expect(screen.getByRole('checkbox', { name: /Rens sluket/ })).toBeChecked());
    const [request] = api.calls('PUT', requirementPath(LANDLORD, SLUKET.id));
    expect(await request.json()).toEqual({ required: true });
  });

  it('shows the server\'s reason for a 409 and offers no retry', async () => {
    fakeApi({
      ...signedInWith([LANDLORD]),
      [`PUT ${requirementPath(LANDLORD, SLUKET.id)}`]: () =>
        json(409, { detail: 'Bare Må-oppgaver kan kreve bildebevis.' }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);

    await userEvent.click(await screen.findByRole('checkbox', { name: /Rens sluket/ }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Bare Må-oppgaver kan kreve bildebevis.');
    expect(screen.queryByRole('button', { name: 'Prøv igjen' })).toBeNull();
  });

  it('retries a failed save with «Prøv igjen»', async () => {
    let attempts = 0;
    const api = fakeApi({
      ...signedInWith([LANDLORD]),
      [`PUT ${requirementPath(LANDLORD, SLUKET.id)}`]: () =>
        ++attempts === 1 ? json(500, { detail: 'boom' }) : json(200, { requires_photo_evidence: true }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);
    await userEvent.click(await screen.findByRole('checkbox', { name: /Rens sluket/ }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Vi fikk ikke lagret kravet om bilde.');

    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));

    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull());
    expect(api.calls('PUT', requirementPath(LANDLORD, SLUKET.id))).toHaveLength(2);
    const [, second] = api.calls('PUT', requirementPath(LANDLORD, SLUKET.id));
    expect(await second.json()).toEqual({ required: true });
  });

  it('says so when no task can require a photo', async () => {
    fakeApi({
      ...signedInWith([LANDLORD]),
      [`GET ${tasksPath(LANDLORD)}`]: () =>
        json(200, { tasks: OLAS_TASKS.map((t) => ({ ...t, may_require_photo_evidence: false })) }),
    });
    renderAt(`/hjem/${LANDLORD.id}/utleier`);

    expect(await screen.findByText('Ingen av oppgavene dine kan kreve bilde ennå.')).toBeInTheDocument();
    expect(screen.queryByRole('checkbox')).toBeNull();
  });

  it('is not shown when the server does not allow the caller to require a photo', async () => {
    fakeApi(signedInWith([{ ...LANDLORD, can_require_photo_evidence: false }]));
    renderAt(`/hjem/${LANDLORD.id}/utleier`);

    await screen.findByLabelText('Melding');
    expect(screen.queryByRole('heading', { name: 'Bildebevis' })).toBeNull();
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

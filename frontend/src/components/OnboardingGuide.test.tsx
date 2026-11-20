// Story 5.3 (FR-16, UX onboarding card): the guide card on the Task Overview, its dismissal, the
// Settings link and the page, one test per matrix row.
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { FREQUENCY_LABELS } from '../api/tasks';
import { GUIDE_MESSAGES } from '../api/onboarding';
import {
  GUIDE_DISCLAIMER,
  OLAS_HOME,
  OLAS_TENANCY,
  fakeApi,
  guidePath,
  guideServer,
  resetApi,
  signedInWith,
} from '../test-utils/fakeApi';

const LANDLORD = { ...OLAS_TENANCY, role: 'landlord' as const, name: 'Utleiers hjem' };

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

const overview = (home: { id: string }) => `/hjem/${home.id}`;

afterEach(resetApi);

describe('The onboarding card on the Task Overview', () => {
  it('names the Home, shows the introduction and the Must tasks with frequencies in words', async () => {
    fakeApi(signedInWith([OLAS_TENANCY]));
    renderAt(overview(OLAS_TENANCY));
    const card = await screen.findByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') });
    expect(within(card).getByText('Her ser du hjemmets oppgaver samlet.')).toBeInTheDocument();
    const items = within(card).getAllByRole('listitem');
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent(`Rens sluket ${FREQUENCY_LABELS[30]}`);
    expect(items[1]).toHaveTextContent(`Vask badet grundig ${FREQUENCY_LABELS[14]}`);
    expect(within(card).getByText(GUIDE_DISCLAIMER)).toBeInTheDocument();
  });

  it('sits above the task list', async () => {
    fakeApi(signedInWith([OLAS_TENANCY]));
    renderAt(overview(OLAS_TENANCY));
    const card = await screen.findByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') });
    const tasks = await screen.findByRole('region', { name: 'Oppgaver' });
    expect(card.compareDocumentPosition(tasks) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('shows the demo marker, and no disclaimer for the fixed fallback text', async () => {
    fakeApi({
      ...signedInWith([OLAS_TENANCY]),
      ...guideServer(OLAS_TENANCY, { source: 'demo', demo: true }),
    });
    renderAt(overview(OLAS_TENANCY));
    expect(await screen.findByText(GUIDE_MESSAGES.demo)).toBeInTheDocument();
  });

  it('has no disclaimer when the server sends none (the fixed text)', async () => {
    fakeApi({
      ...signedInWith([OLAS_TENANCY]),
      ...guideServer(OLAS_TENANCY, { source: 'fallback', disclaimer: null }),
    });
    renderAt(overview(OLAS_TENANCY));
    await screen.findByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') });
    expect(screen.queryByText(GUIDE_DISCLAIMER)).not.toBeInTheDocument();
  });

  it('says plainly when the Home has no Must tasks', async () => {
    fakeApi({ ...signedInWith([OLAS_TENANCY]), ...guideServer(OLAS_TENANCY, { must_tasks: [] }) });
    renderAt(overview(OLAS_TENANCY));
    expect(await screen.findByText(GUIDE_MESSAGES.noMust)).toBeInTheDocument();
  });

  it('is gone for a Tenant who already dismissed it', async () => {
    fakeApi({ ...signedInWith([OLAS_TENANCY]), ...guideServer(OLAS_TENANCY, { dismissed: true }) });
    renderAt(overview(OLAS_TENANCY));
    await screen.findByRole('region', { name: 'Oppgaver' });
    expect(screen.queryByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') })).not.toBeInTheDocument();
  });

  it('«Skjul» removes the card at once and keeps it gone on a reload', async () => {
    const server = fakeApi(signedInWith([OLAS_TENANCY]));
    const first = renderAt(overview(OLAS_TENANCY));
    await screen.findByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') });
    await userEvent.click(screen.getByRole('button', { name: GUIDE_MESSAGES.dismiss }));
    await waitFor(() =>
      expect(screen.queryByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') })).not.toBeInTheDocument(),
    );
    expect(server.calls('POST', `${guidePath(OLAS_TENANCY)}/dismiss`)).toHaveLength(1);
    // A fresh page load asks the server, which remembers.
    first.unmount();
    renderAt(overview(OLAS_TENANCY));
    await screen.findByRole('region', { name: 'Oppgaver' });
    expect(screen.queryByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') })).not.toBeInTheDocument();
  });

  it('puts the card back with a message when the dismissal fails', async () => {
    fakeApi({ ...signedInWith([OLAS_TENANCY]), ...guideServer(OLAS_TENANCY, {}, 500) });
    renderAt(overview(OLAS_TENANCY));
    await screen.findByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') });
    await userEvent.click(screen.getByRole('button', { name: GUIDE_MESSAGES.dismiss }));
    expect(await screen.findByRole('alert')).toHaveTextContent(GUIDE_MESSAGES.dismissFailed);
    expect(screen.getByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: GUIDE_MESSAGES.dismiss })).toBeEnabled();
  });

  it('never gets in the way of the tasks when the guide cannot be loaded', async () => {
    fakeApi({ ...signedInWith([OLAS_TENANCY]), [`GET ${guidePath(OLAS_TENANCY)}`]: () => new Response(null, { status: 500 }) });
    renderAt(overview(OLAS_TENANCY));
    expect(await screen.findByRole('region', { name: 'Oppgaver' })).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: GUIDE_MESSAGES.heading('Storgata 12') })).not.toBeInTheDocument();
  });

  it('is not shown to the Landlord, and the Landlord does not fetch it for the card', async () => {
    const server = fakeApi(signedInWith([LANDLORD]));
    renderAt(overview(LANDLORD));
    await screen.findByRole('region', { name: 'Oppgaver' });
    expect(screen.queryByRole('region', { name: GUIDE_MESSAGES.heading('Utleiers hjem') })).not.toBeInTheDocument();
    expect(server.calls('GET', guidePath(LANDLORD))).toHaveLength(0);
  });

  it('is not asked for in a Household Home', async () => {
    const server = fakeApi(signedInWith([OLAS_HOME]));
    renderAt(overview(OLAS_HOME));
    await screen.findByRole('region', { name: 'Oppgaver' });
    expect(server.calls('GET', guidePath(OLAS_HOME))).toHaveLength(0);
  });
});

describe('Reading the guide again', () => {
  it('has «Velkomstguide» under Settings for a Tenant, and it opens the page', async () => {
    fakeApi(signedInWith([OLAS_TENANCY, OLAS_HOME]));
    renderAt('/innstillinger');
    const link = await screen.findByRole('link', { name: 'Velkomstguide for Storgata 12' });
    expect(screen.queryByRole('link', { name: `Velkomstguide for ${OLAS_HOME.name}` })).not.toBeInTheDocument();
    await userEvent.click(link);
    expect(window.location.pathname).toBe(`/hjem/${OLAS_TENANCY.id}/velkommen`);
    expect(await screen.findByRole('heading', { level: 1, name: GUIDE_MESSAGES.heading('Storgata 12') })).toBeInTheDocument();
    // Dismissed or not, the page shows it, with no «Skjul».
    expect(screen.queryByRole('button', { name: GUIDE_MESSAGES.dismiss })).not.toBeInTheDocument();
  });

  it('shows a dismissed guide on the page, so it can always be read again', async () => {
    fakeApi({ ...signedInWith([OLAS_TENANCY]), ...guideServer(OLAS_TENANCY, { dismissed: true }) });
    renderAt(`/hjem/${OLAS_TENANCY.id}/velkommen`);
    expect(await screen.findByText('Her ser du hjemmets oppgaver samlet.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: GUIDE_MESSAGES.backToHome })).toHaveAttribute('href', overview(OLAS_TENANCY));
  });

  it('lets the Landlord read it from Settings', async () => {
    fakeApi(signedInWith([LANDLORD]));
    renderAt(`/hjem/${LANDLORD.id}/velkommen`);
    expect(await screen.findByRole('heading', { level: 1, name: GUIDE_MESSAGES.heading('Utleiers hjem') })).toBeInTheDocument();
  });

  it('sends a Household Home back to its overview', async () => {
    fakeApi(signedInWith([OLAS_HOME]));
    renderAt(`/hjem/${OLAS_HOME.id}/velkommen`);
    await waitFor(() => expect(window.location.pathname).toBe(overview(OLAS_HOME)));
  });

  it('sends an unknown Home to the start', async () => {
    fakeApi(signedInWith([OLAS_TENANCY]));
    renderAt('/hjem/00000000-0000-4000-8000-00000000dead/velkommen');
    await waitFor(() => expect(window.location.pathname).not.toContain('velkommen'));
  });

  it('goes back to the overview when the server says the Home has no guide yet (404)', async () => {
    fakeApi({
      ...signedInWith([OLAS_TENANCY]),
      [`GET ${guidePath(OLAS_TENANCY)}`]: () => new Response(JSON.stringify({ detail: 'Ingen guide.' }), { status: 404, headers: { 'content-type': 'application/json' } }),
    });
    renderAt(`/hjem/${OLAS_TENANCY.id}/velkommen`);
    await waitFor(() => expect(window.location.pathname).toBe(overview(OLAS_TENANCY)));
  });
});

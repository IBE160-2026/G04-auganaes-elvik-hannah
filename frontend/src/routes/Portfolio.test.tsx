// Story 6.1 (FR-20, FR-21, UX-DR36): the Portfolio at /portefolje, one test per row of the spec's
// matrix and per acceptance criterion that the frontend owns.
import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import type { Home } from '../api/homes';
import { PORTFOLIO_MESSAGES, type Portfolio as PortfolioBody, type PortfolioHome } from '../api/portfolio';
import {
  OLAS_HOME,
  fakeApi,
  homesResponse,
  json,
  resetApi,
  signedInWith,
  type Handler,
} from '../test-utils/fakeApi';
import { PULL_THRESHOLD } from './usePullToRefresh';

const LANDLORD_HOME: Home = {
  ...OLAS_HOME,
  type: 'landlord',
  role: 'landlord',
  can_leave: false,
  can_broadcast: true,
  can_set_cadence: true,
  can_require_photo_evidence: true,
};
const STORGATA: Home = { ...LANDLORD_HOME, id: '00000000-0000-4000-8000-0000000000c1', name: 'Storgata 12' };
const BAKGATA: Home = { ...LANDLORD_HOME, id: '00000000-0000-4000-8000-0000000000c2', name: 'Bakgata 3' };
const NYGATA: Home = { ...LANDLORD_HOME, id: '00000000-0000-4000-8000-0000000000c3', name: 'Nygata 7' };

const BEHIND: PortfolioHome = {
  home_id: STORGATA.id,
  name: STORGATA.name,
  status: 'behind',
  overdue_tasks: [
    { task_id: 't1', name: 'Rens sluket', due_on: '2026-11-12', days_overdue: 9 },
    { task_id: 't2', name: 'Vaske bad', due_on: '2026-11-20', days_overdue: 1 },
  ],
  due_soon_count: 1,
};
const ON_TRACK: PortfolioHome = {
  home_id: BAKGATA.id,
  name: BAKGATA.name,
  status: 'on_track',
  overdue_tasks: [],
  due_soon_count: 0,
};
const NOT_SET_UP: PortfolioHome = {
  home_id: NYGATA.id,
  name: NYGATA.name,
  status: 'not_set_up',
  overdue_tasks: [],
  due_soon_count: 0,
};

const homes = (list: readonly Home[] = [STORGATA, BAKGATA, NYGATA], hasPortfolio = true): Record<string, Handler> => ({
  ...signedInWith(list),
  'GET /api/homes': () => json(200, homesResponse(list, ['landlord'], null, hasPortfolio)),
});

const body = (...rows: PortfolioHome[]): PortfolioBody => ({ homes: rows });

function portfolioServer(rows: PortfolioBody = body(BEHIND, ON_TRACK, NOT_SET_UP), extra: Record<string, Handler> = {}) {
  return fakeApi({ ...homes(), 'GET /api/portfolio': () => json(200, rows), ...extra });
}

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

// jsdom matches no media query by default (test-setup.ts): the narrow, one-column layout.
const originalMatchMedia = window.matchMedia;
function useWideScreen() {
  window.matchMedia = ((query: string) => ({
    ...originalMatchMedia(query),
    matches: true,
  })) as typeof window.matchMedia;
}

afterEach(() => {
  window.matchMedia = originalMatchMedia;
  resetApi();
});

describe('Portfolio', () => {
  it('shows each Home with its status in words, behind first, from the server', async () => {
    portfolioServer();
    renderAt('/portefolje');

    const list = within(await screen.findByRole('region', { name: 'Hjem' }));
    const rows = list.getAllByRole('link');
    expect(rows[0]).toHaveTextContent('Storgata 12');
    expect(within(rows[0]).getByText('Forsinket')).toBeInTheDocument();
    expect(rows[0]).toHaveTextContent('2 forfalte Må-oppgaver');
    expect(rows[0]).toHaveTextContent('1 Må-oppgave snart forfalt');
    expect(within(rows[1]).getByText('Alt i orden')).toBeInTheDocument();
    expect(within(rows[2]).getByText('Ikke satt opp')).toBeInTheDocument();
  });

  it('opens the Home admin page from a row on a narrow screen', async () => {
    portfolioServer();
    renderAt('/portefolje');

    const row = (await screen.findAllByRole('link', { name: /Storgata 12/ }))[0];

    expect(row).toHaveAttribute('href', `/hjem/${STORGATA.id}/utleier`);
    expect(screen.queryByRole('region', { name: 'Storgata 12' })).not.toBeInTheDocument();
  });

  it('shows a detail column on a wide screen, and selecting a row changes it', async () => {
    useWideScreen();
    portfolioServer();
    renderAt('/portefolje');

    const detail = within(await screen.findByRole('region', { name: 'Storgata 12' }));
    expect(detail.getByText('Rens sluket')).toBeInTheDocument();
    expect(detail.getByText('9 dager forsinket')).toBeInTheDocument();
    expect(detail.getByText('1 dag forsinket')).toBeInTheDocument();
    expect(detail.getByRole('link', { name: 'Administrer hjemmet' })).toHaveAttribute(
      'href',
      `/hjem/${STORGATA.id}/utleier`,
    );

    await userEvent.click(screen.getByRole('button', { name: /Bakgata 3/ }));

    const other = within(screen.getByRole('region', { name: 'Bakgata 3' }));
    expect(other.getByText(PORTFOLIO_MESSAGES.noOverdue)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Bakgata 3/ })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /Storgata 12/ })).toHaveAttribute('aria-pressed', 'false');
  });

  it('shows one skeleton row per known Landlord Home while the Portfolio loads', async () => {
    fakeApi({ ...homes(), 'GET /api/portfolio': () => new Promise<Response>(() => {}) });
    renderAt('/portefolje');

    const skeleton = await screen.findByTestId('portfolio-skeleton');

    expect(skeleton.querySelectorAll('li')).toHaveLength(3);
  });

  it('shows an inline error with a retry, not a blank screen', async () => {
    let fail = true;
    const server = fakeApi({
      ...homes(),
      'GET /api/portfolio': () => (fail ? json(500, { detail: 'x' }) : json(200, body(BEHIND, ON_TRACK))),
    });
    renderAt('/portefolje');

    expect(await screen.findByRole('alert')).toHaveTextContent(PORTFOLIO_MESSAGES.loadFailed);
    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));

    expect(await screen.findByText('Forsinket')).toBeInTheDocument();
    expect(server.calls('GET', '/api/portfolio')).toHaveLength(2);
  });

  it('sends a Landlord without a Portfolio to their Home, with no tab', async () => {
    fakeApi({ ...homes([STORGATA], false), 'GET /api/portfolio': () => json(403, { detail: 'x' }) });
    renderAt('/portefolje');

    await vi.waitFor(() => expect(window.location.pathname).toBe(`/hjem/${STORGATA.id}`));
    const nav = await screen.findByRole('navigation', { name: 'Hovedmeny' });
    expect(screen.queryByRole('heading', { name: 'Portefølje' })).not.toBeInTheDocument();
    expect(within(nav).queryByRole('link', { name: 'Portefølje' })).not.toBeInTheDocument();
  });

  it('shows no load error when the server answers 403, and the Homes refetch routes away', async () => {
    let portfolio = true;
    const server = fakeApi({
      ...signedInWith([STORGATA, BAKGATA]),
      'GET /api/homes': () => json(200, homesResponse([STORGATA, BAKGATA], ['landlord'], null, portfolio)),
      'GET /api/portfolio': () => {
        portfolio = false;
        return json(403, { detail: 'Du har ikke en portefølje.' });
      },
    });
    renderAt('/portefolje');

    await screen.findByRole('heading', { name: 'Portefølje' });
    await vi.waitFor(() => expect(server.calls('GET', '/api/homes').length).toBeGreaterThan(1));
    await vi.waitFor(() => expect(window.location.pathname).not.toBe('/portefolje'));
    expect(screen.queryByText(PORTFOLIO_MESSAGES.loadFailed)).not.toBeInTheDocument();
  });

  it('refetches from «Oppdater» and announces it', async () => {
    const server = portfolioServer();
    renderAt('/portefolje');
    await screen.findByText('Forsinket');

    await userEvent.click(screen.getByRole('button', { name: 'Oppdater' }));

    expect(await screen.findByText(PORTFOLIO_MESSAGES.refreshed)).toBeInTheDocument();
    expect(server.calls('GET', '/api/portfolio')).toHaveLength(2);
  });

  it('refetches on a pull from the top, and not on a short one', async () => {
    const server = portfolioServer();
    renderAt('/portefolje');
    await screen.findByText('Forsinket');
    const columns = document.querySelector('.portfolio__columns') as HTMLElement;

    fireEvent.touchStart(columns, { touches: [{ clientY: 100 }] });
    fireEvent.touchMove(columns, { touches: [{ clientY: 100 + PULL_THRESHOLD / 2 }] });
    fireEvent.touchEnd(columns);
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(server.calls('GET', '/api/portfolio')).toHaveLength(1);

    fireEvent.touchStart(columns, { touches: [{ clientY: 100 }] });
    fireEvent.touchMove(columns, { touches: [{ clientY: 100 + PULL_THRESHOLD }] });
    fireEvent.touchEnd(columns);

    expect(await screen.findByText(PORTFOLIO_MESSAGES.refreshed)).toBeInTheDocument();
    expect(server.calls('GET', '/api/portfolio')).toHaveLength(2);
  });
});

describe('Portfolio tab', () => {
  it('shows «Portefølje» only when the server says the caller has a Portfolio', async () => {
    fakeApi(homes([STORGATA, BAKGATA], true));
    renderAt(`/hjem/${STORGATA.id}`);
    const nav = await screen.findByRole('navigation', { name: 'Hovedmeny' });
    expect(within(nav).getByRole('link', { name: 'Portefølje' })).toHaveAttribute('href', '/portefolje');
  });

  it('is absent for a Landlord with one Home', async () => {
    fakeApi(homes([STORGATA], false));
    renderAt(`/hjem/${STORGATA.id}`);
    const nav = await screen.findByRole('navigation', { name: 'Hovedmeny' });
    expect(within(nav).queryByRole('link', { name: 'Portefølje' })).not.toBeInTheDocument();
  });
});

// Story 6.1 (FR-20, FR-21, UX-DR36): the Landlord Portfolio at /portefolje, one row per Landlord
// Home with its status in words («Forsinket», «Alt i orden», «Ikke satt opp») from the server,
// never colour alone. From the tablet width a second column shows the selected Home's overdue Må
// tasks; below it a row is a link straight to «Administrer hjemmet» (/hjem/<id>/utleier). A pull
// from the top or «Oppdater» refetches and announces «Oppdatert». Whether the caller has a
// Portfolio is the server's has_portfolio, so a Landlord with one Home is sent to "/". Cold load
// shows one skeleton row per Landlord Home the Homes list already knows. A 403 is the global
// handler's, which refetches the Homes, and the guard then routes.
import { useState, useSyncExternalStore } from 'react';
import { Link, Navigate } from 'react-router';
import { ApiError } from '../api/errors';
import type { Home } from '../api/homes';
import {
  PORTFOLIO_MESSAGES,
  daysOverdueText,
  dueSoonText,
  overdueCountText,
  type PortfolioHome,
} from '../api/portfolio';
import { useHomes, usePortfolio } from '../api/queries';
import { StatusTag } from '../components/StatusTag';
import { HomesLoadError } from './HomesLoadError';
import { useFocusOnMount } from './useFocusOnMount';
import { usePullToRefresh } from './usePullToRefresh';
import './AuthForm.css';
import './Portfolio.css';

// Tablet and up: the app shell's breakpoint, 37.5 em (600 CSS px), also written in Portfolio.css.
const TABLET_EM = 37.5;
const TWO_COLUMNS = `(min-width: ${TABLET_EM}em)`;

function subscribe(onChange: () => void) {
  const query = window.matchMedia?.(TWO_COLUMNS);
  query?.addEventListener('change', onChange);
  return () => query?.removeEventListener('change', onChange);
}

function useTwoColumns(): boolean {
  return useSyncExternalStore(subscribe, () => window.matchMedia?.(TWO_COLUMNS).matches ?? false);
}

function isForbidden(error: Error | null): boolean {
  return error instanceof ApiError && error.status === 403;
}

const adminPath = (homeId: string) => `/hjem/${homeId}/utleier`;

export function Portfolio() {
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  if (!homes.data.has_portfolio) return <Navigate to="/" replace />;

  const landlordHomes = homes.data.homes.filter((home) => home.role === 'landlord');
  return <PortfolioPage landlordHomes={landlordHomes} />;
}

function PortfolioPage({ landlordHomes }: { landlordHomes: readonly Home[] }) {
  const portfolio = usePortfolio();
  const titleRef = useFocusOnMount<HTMLHeadingElement>();
  const [announcement, setAnnouncement] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const twoColumns = useTwoColumns();

  async function refresh() {
    if (refreshing) return;
    // Cleared first, so a second «Oppdatert» in a row is announced again.
    setAnnouncement('');
    setRefreshing(true);
    const result = await portfolio.refetch();
    setRefreshing(false);
    if (!result.isError) setAnnouncement(PORTFOLIO_MESSAGES.refreshed);
    else if (!isForbidden(result.error)) {
      setAnnouncement(PORTFOLIO_MESSAGES.refreshFailed);
    }
  }

  const { pulled, handlers } = usePullToRefresh(() => void refresh());
  const rows = portfolio.data?.homes;
  const selected = rows?.find((row) => row.home_id === selectedId) ?? rows?.[0];

  return (
    <div className="portfolio">
      <header className="portfolio__header">
        <h1 ref={titleRef} tabIndex={-1} className="portfolio__title">
          Portefølje
        </h1>
        <button
          type="button"
          className="portfolio__secondary"
          onClick={() => void refresh()}
          disabled={refreshing}
        >
          Oppdater
        </button>
      </header>
      {/* Always in the DOM, so the text is announced when it arrives. */}
      <p className="portfolio__visually-hidden" aria-live="polite">
        {announcement}
      </p>
      <div className="portfolio__columns" aria-busy={portfolio.isPending || refreshing || undefined} {...handlers}>
        <p className={`portfolio__pull${pulled ? ' portfolio__pull--ready' : ''}`} aria-hidden="true">
          Slipp for å oppdatere
        </p>
        {rows ? (
          <>
            <section className="portfolio__list" aria-labelledby="portfolio-homes">
              <h2 id="portfolio-homes" className="portfolio__visually-hidden">
                Hjem
              </h2>
              <ul className="portfolio__rows">
                {rows.map((row) => (
                  <li key={row.home_id}>
                    <Row
                      row={row}
                      twoColumns={twoColumns}
                      selected={twoColumns && row.home_id === selected?.home_id}
                      onSelect={() => setSelectedId(row.home_id)}
                    />
                  </li>
                ))}
              </ul>
            </section>
            {twoColumns && selected && <Detail row={selected} />}
          </>
        ) : portfolio.isError && !isForbidden(portfolio.error) ? (
          <div className="portfolio__error">
            <p className="auth-form__error" role="alert">
              {PORTFOLIO_MESSAGES.loadFailed}
            </p>
            <button type="button" className="portfolio__secondary" onClick={() => void portfolio.refetch()}>
              Prøv igjen
            </button>
          </div>
        ) : (
          <>
            <p className="portfolio__visually-hidden">Henter porteføljen …</p>
            <ul className="portfolio__rows" aria-hidden="true" data-testid="portfolio-skeleton">
              {landlordHomes.map((home) => (
                <li key={home.id} className="portfolio__skeleton-row" />
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}

function Summary({ row }: { row: PortfolioHome }) {
  const lines = [
    row.overdue_tasks.length > 0 ? overdueCountText(row.overdue_tasks.length) : null,
    row.due_soon_count > 0 ? dueSoonText(row.due_soon_count) : null,
  ].filter(Boolean);
  return (
    <>
      <span className="portfolio__name">{row.name}</span>
      <StatusTag status={row.status} />
      {lines.length > 0 && <span className="portfolio__meta">{lines.join(' · ')}</span>}
    </>
  );
}

function Row({
  row,
  twoColumns,
  selected,
  onSelect,
}: {
  row: PortfolioHome;
  twoColumns: boolean;
  selected: boolean;
  onSelect: () => void;
}) {
  // Narrow: the row opens the Home's admin page. Wide: it selects the Home for the detail column.
  if (!twoColumns) {
    return (
      <Link to={adminPath(row.home_id)} className="portfolio__row">
        <Summary row={row} />
      </Link>
    );
  }
  return (
    <button
      type="button"
      className="portfolio__row"
      aria-pressed={selected}
      aria-controls="portfolio-detail"
      onClick={onSelect}
    >
      <Summary row={row} />
    </button>
  );
}

function Detail({ row }: { row: PortfolioHome }) {
  return (
    <section id="portfolio-detail" className="portfolio__detail" aria-labelledby="portfolio-detail-title">
      <h2 id="portfolio-detail-title" className="portfolio__detail-title">
        {row.name}
      </h2>
      <StatusTag status={row.status} />
      {row.overdue_tasks.length > 0 ? (
        <ul className="portfolio__overdue">
          {row.overdue_tasks.map((task) => (
            <li key={task.task_id}>
              <span>{task.name}</span> <span className="portfolio__meta">{daysOverdueText(task.days_overdue)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="portfolio__meta">{PORTFOLIO_MESSAGES.noOverdue}</p>
      )}
      {row.due_soon_count > 0 && <p className="portfolio__meta">{dueSoonText(row.due_soon_count)}</p>}
      <Link to={adminPath(row.home_id)} className="portfolio__link">
        Administrer hjemmet
      </Link>
    </section>
  );
}

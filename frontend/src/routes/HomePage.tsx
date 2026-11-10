// Story 1.3: the post-creation landing page. Shows the newest Home, the user's Role in it and
// "Logg ut"; Landlords also see their Homes. "Opprett nytt hjem" shows whenever the server's
// allowed_types offers something (Story 1.9: a Landlord Home always). Task Overview replaces this
// page in Stories 2.1–2.2, and the tab bar comes with Story 2.2. Story 1.4: links to
// "Medlemmer og invitasjon" for the shown Home, and for each of a Landlord's Homes.
// Story 1.8: shows «Du har forlatt «X».» when a Landlord who also lived in a Household left it.
// Story 2.1 (decisions 1, 7 and 8): a minimal task list under «Oppgaver» until Story 2.2 replaces
// this page. A shown Home without Tasks sends whoever may set it up to Task Setup; a Tenant
// waits for the Landlord. «Dine hjem» offers «Sett opp oppgaver» for a Landlord's other Homes.
import { Link, Navigate } from 'react-router';
import { ROLE_LABELS, TYPE_LABELS, type Home } from '../api/homes';
import { useHomes, useMe, useSignOut, useTasks } from '../api/queries';
import { FREQUENCY_LABELS, TASK_MESSAGES, formatDueOn } from '../api/tasks';
import { Badge } from '../components/Badge';
import { PendingNotice } from '../components/PendingNotice';
import { PrimaryButton } from '../components/PrimaryButton';
import { HomesLoadError } from './HomesLoadError';
import './AuthForm.css';
import './HomePage.css';

export function HomePage() {
  const me = useMe();
  const homes = useHomes();
  const signOut = useSignOut();

  if (homes.isPending) return <p role="status">Laster …</p>;
  // A failed background refetch keeps the cached data; only a load with nothing to show is an error.
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  // Only a loaded, empty list sends the user to Create Home.
  if (homes.data.homes.length === 0) return <Navigate to="/nytt-hjem" replace />;

  const [home] = homes.data.homes;
  // From the server's has_tasks, so the redirect never waits for the tasks request.
  if (!home.has_tasks && home.can_set_up_tasks) {
    return <Navigate to={setupPath(home)} replace />;
  }
  const isLandlord = homes.data.homes.some((h) => h.role === 'landlord');
  const canCreate = homes.data.allowed_types.length > 0;
  const firstName = me.data?.name.split(' ')[0];

  return (
    <div className="home-page">
      <PendingNotice className="home-page__notice" />
      <h1 className="home-page__title">{home.name}</h1>
      {home.type === 'household' ? (
        <p className="home-page__lead">Velkommen hjem{firstName ? `, ${firstName}` : ''}! Her deler dere på husarbeidet.</p>
      ) : (
        <p className="home-page__lead">Du er logget inn som {me.data?.name}.</p>
      )}
      <dl className="home-page__facts">
        <div>
          <dt>Type</dt>
          <dd>{TYPE_LABELS[home.type]}</dd>
        </div>
        <div>
          <dt>Din rolle</dt>
          <dd>{ROLE_LABELS[home.role]}</dd>
        </div>
      </dl>
      <section className="home-page__section" aria-labelledby="home-page-tasks">
        <h2 id="home-page-tasks" className="home-page__subtitle">
          Oppgaver
        </h2>
        {home.has_tasks ? (
          <TaskList key={home.id} home={home} />
        ) : (
          <p className="home-page__meta">{TASK_MESSAGES.tenantWaiting}</p>
        )}
      </section>
      <Link to={`/hjem/${home.id}/medlemmer`} className="home-page__link">
        Medlemmer og invitasjon
      </Link>
      {isLandlord && (
        <section className="home-page__section" aria-labelledby="home-page-homes">
          <h2 id="home-page-homes" className="home-page__subtitle">
            Dine hjem
          </h2>
          <ul className="home-page__list">
            {homes.data.homes.map((h) => (
              <li key={h.id}>
                {h.name} <span className="home-page__meta">({ROLE_LABELS[h.role]})</span>{' '}
                <Link
                  to={`/hjem/${h.id}/medlemmer`}
                  className="home-page__list-link"
                  aria-label={`Medlemmer og invitasjon for ${h.name}`}
                >
                  Medlemmer
                </Link>
                {h.can_set_up_tasks && !h.has_tasks && (
                  <>
                    {' '}
                    <Link
                      to={setupPath(h)}
                      className="home-page__list-link"
                      aria-label={`Sett opp oppgaver for ${h.name}`}
                    >
                      Sett opp oppgaver
                    </Link>
                  </>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
      {canCreate && (
        <Link to="/nytt-hjem" className="home-page__link">
          Opprett nytt hjem
        </Link>
      )}
      <PrimaryButton onClick={() => signOut.mutate()} pending={signOut.isPending}>
        Logg ut
      </PrimaryButton>
    </div>
  );
}

function setupPath(home: Home): string {
  return `/hjem/${home.id}/oppgaveoppsett`;
}

// Rendered only for a Home with Tasks. A failed load stays in this section, so the rest of the
// page (Medlemmer, Logg ut) is still there.
function TaskList({ home }: { home: Home }) {
  const tasks = useTasks(home.id);

  if (tasks.data) {
    return (
      <ul className="home-page__tasks">
        {tasks.data.map((task) => (
          <li key={task.id} className="home-page__task">
            <span className="home-page__task-name">{task.name}</span>
            <span className="home-page__task-meta">
              <Badge classification={task.classification} />
              <span>{FREQUENCY_LABELS[task.frequency_days]}</span>
              <span>Neste gang: {formatDueOn(task.due_on)}</span>
            </span>
          </li>
        ))}
      </ul>
    );
  }
  if (tasks.isError) {
    return (
      <>
        <p className="auth-form__error" role="alert">
          {TASK_MESSAGES.loadFailed}
        </p>
        <button
          type="button"
          className="home-page__secondary"
          aria-label="Prøv å hente oppgavene igjen"
          onClick={() => void tasks.refetch()}
        >
          Prøv igjen
        </button>
      </>
    );
  }
  // No role="status": the Homes loading above already uses it.
  return <p className="home-page__meta">Henter oppgaver …</p>;
}

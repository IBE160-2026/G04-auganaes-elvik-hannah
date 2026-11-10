// Story 2.2 (FR-6, FR-21, UX-DR19/20/36/41): one Task Overview per Home at /hjem/<id>. Every
// Task is listed, Must first, in the server's order (domain/tasks.tasks_of); the frontend never
// re-sorts. Each row shows the Må/Bør badge and the due state in words («Forfalt», «Snart
// forfall») from the server's due_status, so colour is never the only signal. Cold load shows
// skeleton rows, nothing due shows an empty-state text above the list (decisions 2 and 10), and a
// pull from the top or «Oppdater» refetches and announces «Oppdatert» (decision 9).
// Guards come from the server's Homes list: a foreign or unknown id goes to "/", a Home without
// Tasks goes to Task Setup for whoever may set it up, and a Tenant sees the waiting text. Only
// after the guards pass is the Home recorded as last used (decision 12).
// The Story 1.8 leave notice («Du har forlatt «X».») is shown here, where "/" lands.
import { useEffect, useRef, useState, type RefObject, type TouchEvent } from 'react';
import { Link, Navigate, useParams } from 'react-router';
import { ApiError } from '../api/errors';
import { ROLE_LABELS, type Home } from '../api/homes';
import { recordLastHome } from '../api/lastHome';
import { useHomes, useTasks } from '../api/queries';
import { useSession } from '../api/session';
import { TASK_MESSAGES, dueText, type Task } from '../api/tasks';
import { Badge } from '../components/Badge';
import { PendingNotice } from '../components/PendingNotice';
import { HomesLoadError } from './HomesLoadError';
import { useFocusOnMount } from './useFocusOnMount';
import './AuthForm.css';
import './TaskOverview.css';

// How far (in CSS pixels) a pull from the top must go before releasing refreshes.
export const PULL_THRESHOLD = 64;
const SKELETON_ROWS = 4;

export function TaskOverview() {
  const { homeId } = useParams();
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  // A failed background refetch keeps the cached data; only a load with nothing to show is an error.
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  const home = homes.data.homes.find((h) => h.id === homeId);
  // Not theirs, gone, or a typo: "/" picks a Home they have (or Create Home).
  if (!home) return <Navigate to="/" replace />;
  // From the server's has_tasks, so the redirect never waits for the tasks request.
  if (!home.has_tasks && home.can_set_up_tasks) {
    return <Navigate to={`/hjem/${home.id}/oppgaveoppsett`} replace />;
  }

  return <Overview key={home.id} home={home} canSwitch={homes.data.homes.length >= 2} />;
}

function Overview({ home, canSwitch }: { home: Home; canSwitch: boolean }) {
  const userId = useSession()?.user.id;
  const titleRef = useFocusOnMount<HTMLHeadingElement>();

  // The guards have passed: this is now the Home "/" opens on this device.
  useEffect(() => {
    recordLastHome(userId, home.id);
  }, [userId, home.id]);

  return (
    <div className="task-overview">
      <PendingNotice className="task-overview__notice" />
      {home.has_tasks ? (
        <TaskSection home={home} titleRef={titleRef} canSwitch={canSwitch} />
      ) : (
        <>
          <Header home={home} titleRef={titleRef} canSwitch={canSwitch} />
          <p className="task-overview__meta">{TASK_MESSAGES.tenantWaiting}</p>
        </>
      )}
    </div>
  );
}

type HeaderProps = {
  home: Home;
  titleRef: RefObject<HTMLHeadingElement | null>;
  canSwitch: boolean;
  onRefresh?: () => void;
  refreshing?: boolean;
};

// Decision 11: Home name, the caller's Role, «Medlemmer og invitasjon», «Bytt hjem» with two or
// more Homes, and «Oppdater» when there is a list to refresh.
function Header({ home, titleRef, canSwitch, onRefresh, refreshing }: HeaderProps) {
  return (
    <div className="task-overview__header">
      <h1 ref={titleRef} tabIndex={-1} className="task-overview__title">
        {home.name}
      </h1>
      <p className="task-overview__meta">{ROLE_LABELS[home.role]}</p>
      <div className="task-overview__actions">
        <Link to={`/hjem/${home.id}/medlemmer`} className="task-overview__link">
          Medlemmer og invitasjon
        </Link>
        {canSwitch && (
          <Link to="/innstillinger#dine-hjem" className="task-overview__link">
            Bytt hjem
          </Link>
        )}
        {onRefresh && (
          <button
            type="button"
            className="task-overview__secondary"
            aria-busy={refreshing || undefined}
            onClick={onRefresh}
          >
            Oppdater
          </button>
        )}
      </div>
    </div>
  );
}

function isForbidden(error: Error | null): boolean {
  return error instanceof ApiError && error.status === 403;
}

function TaskSection({ home, titleRef, canSwitch }: Omit<HeaderProps, 'onRefresh' | 'refreshing'>) {
  const tasks = useTasks(home.id);
  const [announcement, setAnnouncement] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [pulled, setPulled] = useState(false);
  const pullStart = useRef<number | null>(null);

  // Decision 9: the document is what scrolls, so the browser's own pull-to-reload is turned off
  // there while the list is shown, and the app's pull is the only one. Restored on unmount.
  useEffect(() => {
    const root = document.documentElement;
    const previous = root.style.overscrollBehaviorY;
    root.style.overscrollBehaviorY = 'contain';
    return () => {
      root.style.overscrollBehaviorY = previous;
    };
  }, []);

  async function refresh() {
    if (refreshing) return;
    // Cleared first, so a second «Oppdatert» in a row is announced again.
    setAnnouncement('');
    setRefreshing(true);
    const result = await tasks.refetch();
    setRefreshing(false);
    if (result.isError) {
      // A 403 is the global handler's; the guards then route.
      if (!isForbidden(result.error)) setAnnouncement(TASK_MESSAGES.refreshFailed);
    } else {
      setAnnouncement(TASK_MESSAGES.refreshed);
    }
  }

  // Pull-to-refresh: only a pull that starts with the page scrolled to the top.
  function onTouchStart(event: TouchEvent) {
    const atTop = (document.scrollingElement?.scrollTop ?? 0) <= 0;
    pullStart.current = atTop ? event.touches[0].clientY : null;
  }

  function onTouchMove(event: TouchEvent) {
    if (pullStart.current === null) return;
    setPulled(event.touches[0].clientY - pullStart.current >= PULL_THRESHOLD);
  }

  function onTouchEnd() {
    const release = pulled;
    pullStart.current = null;
    setPulled(false);
    if (release) void refresh();
  }

  return (
    <>
      <Header
        home={home}
        titleRef={titleRef}
        canSwitch={canSwitch}
        onRefresh={() => void refresh()}
        refreshing={refreshing}
      />
      {/* Always in the DOM, so the text is announced when it arrives. */}
      <p className="task-overview__visually-hidden" aria-live="polite">
        {announcement}
      </p>
      <section
        className="task-overview__tasks"
        aria-labelledby="task-overview-tasks"
        aria-busy={tasks.isPending || refreshing || undefined}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
        onTouchCancel={() => {
          pullStart.current = null;
          setPulled(false);
        }}
      >
        <h2 id="task-overview-tasks" className="task-overview__visually-hidden">
          Oppgaver
        </h2>
        <p className={`task-overview__pull${pulled ? ' task-overview__pull--ready' : ''}`} aria-hidden="true">
          Slipp for å oppdatere
        </p>
        <TaskListBody home={home} tasks={tasks} />
      </section>
    </>
  );
}

function TaskListBody({ home, tasks }: { home: Home; tasks: ReturnType<typeof useTasks> }) {
  if (tasks.data) {
    const nothingDue = tasks.data.every((task) => task.due_status === 'later');
    return (
      <>
        {nothingDue && (
          <p className="task-overview__empty">
            {home.role === 'landlord' ? TASK_MESSAGES.nothingDueLandlord : TASK_MESSAGES.nothingDueHousehold}
          </p>
        )}
        <ul className="task-overview__list">
          {tasks.data.map((task) => (
            <li key={task.id}>
              <TaskRow home={home} task={task} />
            </li>
          ))}
        </ul>
      </>
    );
  }
  if (tasks.isError) {
    // A 403 shows nothing inline: the global handler refetches and the guards route.
    if (isForbidden(tasks.error)) return null;
    return (
      <>
        <p className="auth-form__error" role="alert">
          {TASK_MESSAGES.loadFailed}
        </p>
        <button
          type="button"
          className="task-overview__secondary"
          aria-label="Prøv å hente oppgavene igjen"
          onClick={() => void tasks.refetch()}
        >
          Prøv igjen
        </button>
      </>
    );
  }
  return (
    <>
      <p className="task-overview__visually-hidden">Henter oppgaver …</p>
      <ul className="task-overview__list" aria-hidden="true" data-testid="task-skeleton">
        {Array.from({ length: SKELETON_ROWS }, (_, index) => (
          <li key={index} className="task-overview__skeleton-row" />
        ))}
      </ul>
    </>
  );
}

// The whole row is one link to Task Detail. The checkbox comes with Story 2.4 (decision 6).
function TaskRow({ home, task }: { home: Home; task: Task }) {
  return (
    <Link to={`/hjem/${home.id}/oppgaver/${task.id}`} className="task-overview__row">
      <span className="task-overview__row-top">
        <span className="task-overview__name">{task.name}</span>
        <Badge classification={task.classification} />
      </span>
      <span className={`task-overview__due task-overview__due--${task.due_status}`}>{dueText(task)}</span>
    </Link>
  );
}

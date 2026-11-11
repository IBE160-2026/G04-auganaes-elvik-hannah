// Story 2.2 (decision 6): a minimal, read-only Task Detail at /hjem/<id>/oppgaver/<taskId>, so a
// row on the Task Overview leads somewhere. Read from the Home's tasks query (no new route);
// Story 2.3 adds editing of Må/Bør and the interval here.
// Guards as on the Task Overview: a foreign or unknown Home goes to "/", a Home without Tasks to
// its overview (which routes on), and a loaded list without this Task back to the overview.
import { Link, Navigate, useParams } from 'react-router';
import { ApiError } from '../api/errors';
import type { Home } from '../api/homes';
import { useHomes, useTasks } from '../api/queries';
import { FREQUENCY_LABELS, TASK_MESSAGES, dueText, type Task } from '../api/tasks';
import { Badge } from '../components/Badge';
import { HomesLoadError } from './HomesLoadError';
import { useFocusOnMount } from './useFocusOnMount';
import './AuthForm.css';
import './TaskDetail.css';

export function TaskDetail() {
  const { homeId, taskId } = useParams();
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  const home = homes.data.homes.find((h) => h.id === homeId);
  if (!home) return <Navigate to="/" replace />;
  if (!home.has_tasks) return <Navigate to={`/hjem/${home.id}`} replace />;

  return <TaskLoader key={home.id} home={home} taskId={taskId} />;
}

function TaskLoader({ home, taskId }: { home: Home; taskId: string | undefined }) {
  const tasks = useTasks(home.id);

  if (tasks.data) {
    const task = tasks.data.find((t) => t.id === taskId);
    // Gone (archived later, Story 2.6) or a typo: back to the list.
    if (!task) return <Navigate to={`/hjem/${home.id}`} replace />;
    return <Detail key={task.id} home={home} task={task} />;
  }
  if (tasks.isError) {
    // A 403 shows nothing inline: the global handler refetches and the guards route.
    if (tasks.error instanceof ApiError && tasks.error.status === 403) return null;
    return (
      <div className="task-detail">
        <p className="auth-form__error" role="alert">
          {TASK_MESSAGES.loadFailed}
        </p>
        <button
          type="button"
          className="task-detail__secondary"
          aria-label="Prøv å hente oppgavene igjen"
          onClick={() => void tasks.refetch()}
        >
          Prøv igjen
        </button>
        <BackLink home={home} />
      </div>
    );
  }
  return <p role="status">Laster …</p>;
}

function Detail({ home, task }: { home: Home; task: Task }) {
  const titleRef = useFocusOnMount<HTMLHeadingElement>();
  return (
    <div className="task-detail">
      <h1 ref={titleRef} tabIndex={-1} className="task-detail__title">
        {task.name}
      </h1>
      <dl className="task-detail__facts">
        <div>
          <dt>Viktighet</dt>
          <dd>
            <Badge classification={task.classification} />
          </dd>
        </div>
        <div>
          <dt>Hvor ofte</dt>
          <dd>{FREQUENCY_LABELS[task.frequency_days]}</dd>
        </div>
        <div>
          <dt>Frist</dt>
          <dd className={`task-detail__due task-detail__due--${task.due_status}`}>{dueText(task)}</dd>
        </div>
      </dl>
      <BackLink home={home} />
    </div>
  );
}

function BackLink({ home }: { home: Home }) {
  return (
    <Link to={`/hjem/${home.id}`} className="task-detail__link">
      Tilbake til oppgavene
    </Link>
  );
}

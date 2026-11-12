// Story 2.2 (decision 6): a minimal Task Detail at /hjem/<id>/oppgaver/<taskId>, so a row on the
// Task Overview leads somewhere. Read from the Home's tasks query (no new route).
// Story 2.3 (FR-5, FR-8, UX-DR30): a Household Member or the Landlord changes Må/Bør and the
// interval here and saves with «Lagre endringer» (decision 2); a Tenant sees the two as locked,
// focusable read-only fields «Satt av utleier». Who may edit is the server's can_adjust_tasks.
// Guards as on the Task Overview: a foreign or unknown Home goes to "/", a Home without Tasks to
// its overview (which routes on), and a loaded list without this Task back to the overview.
// Story 2.4 (decision 6): Detail shows the completion note read-only under «Status», with a
// tick still on its way merged in as on the overview; completing from here comes with Epic 4.
// Story 2.6 (FR-24): whoever may adjust Tasks also sees «Fjern oppgaven», an inline confirmation
// that archives the Task and lands on the overview with «Fjernet «X».».
import { useId, useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate, useParams } from 'react-router';
import { ApiError } from '../api/errors';
import type { Home } from '../api/homes';
import { useAdjustTask, useArchiveTask, useHomes, useTasksWithPending, type TaskView } from '../api/queries';
import {
  CLASSIFICATION_LABELS,
  FREQUENCIES,
  FREQUENCY_LABELS,
  PENDING_COMPLETION_TEXT,
  TASK_MESSAGES,
  completionText,
  dueText,
  type Classification,
  type Frequency,
  type Task,
  type TaskChanges,
} from '../api/tasks';
import { ConfirmAction } from '../components/ConfirmAction';
import { PrimaryButton } from '../components/PrimaryButton';
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
  const { tasks, views } = useTasksWithPending(home.id);

  if (views) {
    const task = views.find((t) => t.id === taskId);
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

function Detail({ home, task }: { home: Home; task: TaskView }) {
  const titleRef = useFocusOnMount<HTMLHeadingElement>();
  const note = task.pending ? PENDING_COMPLETION_TEXT : task.completion && completionText(task.completion);
  return (
    <div className="task-detail">
      <h1 ref={titleRef} tabIndex={-1} className="task-detail__title">
        {task.name}
      </h1>
      {home.can_adjust_tasks ? <AdjustForm home={home} task={task} /> : <LockedFields task={task} />}
      <dl className="task-detail__facts">
        <div>
          <dt>Frist</dt>
          <dd className={`task-detail__due task-detail__due--${task.due_status}`}>{dueText(task)}</dd>
        </div>
        {note && (
          <div>
            <dt>Status</dt>
            <dd className="task-detail__done">{note}</dd>
          </div>
        )}
      </dl>
      {home.can_adjust_tasks && <RemoveTask home={home} task={task} />}
      <BackLink home={home} />
    </div>
  );
}

/** Story 2.6: «Fjern oppgaven» with an inline confirmation (EXPERIENCE.md, Remove Task). */
function RemoveTask({ home, task }: { home: Home; task: Task }) {
  const archive = useArchiveTask(home.id);
  const navigate = useNavigate();
  // 403: the global handler routes. 404: gone already; the refetch sends the user to the list.
  const failed = archive.error instanceof ApiError && [403, 404].includes(archive.error.status);

  return (
    <ConfirmAction
      label="Fjern oppgaven"
      ariaLabel={`Fjern oppgaven «${task.name}»`}
      explanation={TASK_MESSAGES.removeExplanation}
      confirmLabel="Ja, fjern oppgaven"
      confirmAriaLabel={`Ja, fjern oppgaven «${task.name}»`}
      onConfirm={(close) =>
        archive.mutate(task, {
          onSuccess: () => navigate(`/hjem/${home.id}`, { replace: true }),
          onError: (error) => {
            if (error instanceof ApiError && error.status === 403) close();
          },
        })
      }
      onCancel={() => archive.reset()}
      pending={archive.isPending}
      error={archive.error && !failed ? TASK_MESSAGES.archiveFailed : null}
    />
  );
}

/** The message for a failed save, or null when another part of the app handles it. */
function saveError(error: Error | null): string | null {
  if (!error) return null;
  if (error instanceof ApiError) {
    // 403: the global handler refetches and the guards route. 404: the tasks refetch and the
    // TaskLoader guard returns to the overview.
    if (error.status === 403 || error.status === 404) return null;
    return error.message;
  }
  // Network failure: the same message as a 5xx (deliberate).
  return TASK_MESSAGES.saveFailed;
}

/**
 * Decision 2: a draft per field, null meaning "show the server's value", so a refetch after
 * another Member's save updates every field this user has not touched. Only fields whose draft
 * differs from the current Task are sent.
 */
function AdjustForm({ home, task }: { home: Home; task: Task }) {
  const adjust = useAdjustTask(home.id);
  const [classification, setClassification] = useState<Classification | null>(null);
  const [frequency, setFrequency] = useState<Frequency | null>(null);
  const [status, setStatus] = useState('');
  const frequencyId = useId();

  const shownClassification = classification ?? task.classification;
  const shownFrequency = frequency ?? task.frequency_days;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const changes: TaskChanges = {};
    if (classification !== null && classification !== task.classification) changes.classification = classification;
    if (frequency !== null && frequency !== task.frequency_days) changes.frequency_days = frequency;
    if (Object.keys(changes).length === 0) {
      adjust.reset();
      setStatus(TASK_MESSAGES.nothingToSave);
      return;
    }
    setStatus('');
    adjust.mutate(
      { taskId: task.id, changes },
      {
        // A field changed again while the save was in flight keeps its newer draft.
        onSuccess: () => {
          if (changes.classification !== undefined) {
            setClassification((draft) => (draft === changes.classification ? null : draft));
          }
          if (changes.frequency_days !== undefined) {
            setFrequency((draft) => (draft === changes.frequency_days ? null : draft));
          }
          setStatus(TASK_MESSAGES.saved);
        },
      },
    );
  }

  function edited() {
    setStatus('');
  }

  const error = saveError(adjust.error);

  return (
    <form className="task-detail__form" onSubmit={handleSubmit} noValidate>
      <fieldset className="task-detail__field">
        <legend className="task-detail__label">Viktighet</legend>
        <div className="task-detail__choices">
          {(['must', 'should'] as const).map((value) => (
            <label key={value} className={`task-detail__pill task-detail__pill--${value}`}>
              <input
                type="radio"
                name={`klassifisering-${task.id}`}
                value={value}
                checked={shownClassification === value}
                onChange={() => {
                  setClassification(value);
                  edited();
                }}
              />
              {CLASSIFICATION_LABELS[value]}
            </label>
          ))}
        </div>
      </fieldset>
      <div className="task-detail__field">
        <label className="task-detail__label" htmlFor={frequencyId}>
          Hvor ofte
        </label>
        <select
          id={frequencyId}
          className="task-detail__select"
          value={shownFrequency}
          onChange={(e) => {
            setFrequency(Number(e.target.value) as Frequency);
            edited();
          }}
        >
          {FREQUENCIES.map((days) => (
            <option key={days} value={days}>
              {FREQUENCY_LABELS[days]}
            </option>
          ))}
        </select>
      </div>
      {error && (
        <p className="auth-form__error" role="alert">
          {error}
        </p>
      )}
      <PrimaryButton type="submit" pending={adjust.isPending}>
        {error ? 'Prøv igjen' : 'Lagre endringer'}
      </PrimaryButton>
      {/* Always in the DOM, so «Lagret» and «Ingen endringer å lagre.» are announced. */}
      <p className="task-detail__status" role="status">
        {status}
      </p>
    </form>
  );
}

/** UX-DR30: a Tenant's view. Read-only inputs, focusable and labelled, never disabled. */
function LockedFields({ task }: { task: Task }) {
  return (
    <div className="task-detail__form">
      <LockedField label="Viktighet" value={CLASSIFICATION_LABELS[task.classification]} />
      <LockedField label="Hvor ofte" value={FREQUENCY_LABELS[task.frequency_days]} />
    </div>
  );
}

function LockedField({ label, value }: { label: string; value: string }) {
  const inputId = useId();
  const reasonId = useId();
  return (
    <div className="task-detail__field">
      <label className="task-detail__label" htmlFor={inputId}>
        {label}
      </label>
      <div className="task-detail__locked">
        <LockGlyph />
        <input
          id={inputId}
          type="text"
          className="task-detail__locked-input"
          value={value}
          readOnly
          aria-readonly="true"
          aria-describedby={reasonId}
        />
      </div>
      <p id={reasonId} className="task-detail__reason">
        {TASK_MESSAGES.lockedByLandlord}
      </p>
    </div>
  );
}

function LockGlyph() {
  return (
    <svg className="task-detail__lock" aria-hidden="true" focusable="false" viewBox="0 0 16 16" width="1em" height="1em">
      <path
        fill="currentColor"
        d="M8 1a3.5 3.5 0 0 0-3.5 3.5V7H4a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1h-.5V4.5A3.5 3.5 0 0 0 8 1Zm-2 6V4.5a2 2 0 1 1 4 0V7H6Z"
      />
    </svg>
  );
}

function BackLink({ home }: { home: Home }) {
  return (
    <Link to={`/hjem/${home.id}`} className="task-detail__link">
      Tilbake til oppgavene
    </Link>
  );
}

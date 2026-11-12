// Story 2.6 (FR-24, FR-4, FR-8, UX "Add Task"): one page at /hjem/<id>/legg-til-oppgave that adds
// one Task, either a catalog type the Home has no active Task for or a custom Task. The catalog's
// recommendations come from the server (useTaskTypes), and which types are missing from the
// Home's own list (useTasks); the server still decides (a 422 says why). A radio group chooses;
// nothing is preselected unless only «Egen oppgave» is left. Switching resets Må/Bør and the
// interval to that choice's defaults and keeps a typed name; choosing «Egen oppgave» moves focus
// to the name field. Who may add is the server's can_adjust_tasks, and the add needs setup to
// have run (has_tasks); other visitors go to the Home's overview. Success lands on the overview
// with the one-time notice «La til «X».».
import { useId, useRef, useState, type FormEvent } from 'react';
import { flushSync } from 'react-dom';
import { Link, Navigate, useNavigate, useParams } from 'react-router';
import { ApiError } from '../api/errors';
import type { Home } from '../api/homes';
import { useAddTask, useHomes, useTasks, useTaskTypes } from '../api/queries';
import {
  CLASSIFICATION_LABELS,
  FREQUENCY_LABELS,
  TASK_MESSAGES,
  type Classification,
  type Frequency,
  type NewTask,
  type TaskType,
} from '../api/tasks';
import { PrimaryButton } from '../components/PrimaryButton';
import { HomesLoadError } from './HomesLoadError';
import { useFocusOnMount } from './useFocusOnMount';
import './AuthForm.css';
import './TaskSetup.css';
import './AddTask.css';

const CUSTOM = 'custom';
const CUSTOM_DEFAULTS = { classification: 'should', frequency: 30 } as const;

export function AddTask() {
  const { homeId } = useParams();
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  const home = homes.data.homes.find((h) => h.id === homeId);
  if (!home) return <Navigate to="/" replace />;
  // A Tenant, or a Home whose setup has not run (the overview routes those who may set it up).
  if (!home.can_adjust_tasks || !home.has_tasks) return <Navigate to={`/hjem/${home.id}`} replace />;

  return <AddPage key={home.id} home={home} />;
}

function AddPage({ home }: { home: Home }) {
  const titleRef = useFocusOnMount<HTMLHeadingElement>();
  const taskTypes = useTaskTypes();
  const tasks = useTasks(home.id);

  const failed = taskTypes.isError || tasks.isError;
  return (
    <div className="task-setup add-task">
      <h1 ref={titleRef} tabIndex={-1} className="task-setup__title">
        Legg til oppgave
      </h1>
      {taskTypes.data && tasks.data ? (
        <AddForm
          home={home}
          catalog={taskTypes.data.task_types}
          active={tasks.data.map((t) => t.task_type)}
          frequencies={taskTypes.data.frequencies}
        />
      ) : failed ? (
        <>
          <p className="auth-form__error" role="alert">
            {taskTypes.isError ? TASK_MESSAGES.typesLoadFailed : TASK_MESSAGES.loadFailed}
          </p>
          <PrimaryButton
            onClick={() => {
              if (taskTypes.isError) void taskTypes.refetch();
              if (tasks.isError) void tasks.refetch();
            }}
          >
            Prøv igjen
          </PrimaryButton>
        </>
      ) : (
        <p className="task-setup__note">Henter forslag …</p>
      )}
      <Link to={`/hjem/${home.id}`} className="task-setup__link">
        Tilbake til oppgavene
      </Link>
    </div>
  );
}

type Draft = { classification: Classification; frequency: Frequency };

function AddForm({
  home,
  catalog,
  active,
  frequencies,
}: {
  home: Home;
  catalog: TaskType[];
  active: (string | null)[];
  frequencies: Frequency[];
}) {
  const add = useAddTask(home.id);
  const navigate = useNavigate();
  const ids = { error: useId(), nameError: useId() };
  const firstRadio = useRef<HTMLInputElement>(null);
  const nameInput = useRef<HTMLInputElement>(null);
  const missing = catalog.filter((t) => !active.includes(t.key));
  // Only «Egen oppgave» left: preselected, so there is something to fill in.
  const [picked, setChoice] = useState<string | null>(missing.length === 0 ? CUSTOM : null);
  // A type another Member added meanwhile is no longer offered; the choice then falls away.
  const choice = picked === CUSTOM || missing.some((t) => t.key === picked) ? picked : null;
  const [draft, setDraft] = useState<Draft>({ ...CUSTOM_DEFAULTS });
  const [name, setName] = useState('');
  const [noChoice, setNoChoice] = useState(false);

  function defaultsOf(key: string): Draft {
    const entry = missing.find((t) => t.key === key);
    return entry
      ? { classification: entry.classification, frequency: entry.frequency_days }
      : { ...CUSTOM_DEFAULTS };
  }

  // A failed add belongs to what was sent; once the user changes something it no longer applies.
  function edited() {
    if (add.isError) add.reset();
  }

  function choose(key: string) {
    edited();
    flushSync(() => {
      setChoice(key);
      setDraft(defaultsOf(key));
      setNoChoice(false);
    });
    if (key === CUSTOM) nameInput.current?.focus();
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (add.isPending) return;
    if (choice === null) {
      // Render the message first, so it is announced together with the focus move.
      flushSync(() => setNoChoice(true));
      firstRadio.current?.focus();
      return;
    }
    const body: NewTask =
      choice === CUSTOM
        ? { name, classification: draft.classification, frequency_days: draft.frequency }
        : { task_type: choice, classification: draft.classification, frequency_days: draft.frequency };
    add.mutate(body, { onSuccess: () => navigate(`/hjem/${home.id}`, { replace: true }) });
  }

  const error = submitError(add.error);
  // A domain 422 about the name belongs at the name field; every other reason at the form.
  const nameError = choice === CUSTOM && add.error instanceof ApiError && add.error.status === 422 ? error : null;
  const formError = nameError ? null : error;

  return (
    <form className="task-setup__form" onSubmit={handleSubmit} noValidate>
      <fieldset className="add-task__group" aria-describedby={noChoice ? ids.error : undefined}>
        <legend className="add-task__legend">Velg oppgave</legend>
        {missing.map((t, index) => (
          <label key={t.key} className="add-task__option">
            <input
              ref={index === 0 ? firstRadio : undefined}
              type="radio"
              name="oppgave"
              value={t.key}
              checked={choice === t.key}
              aria-invalid={index === 0 && noChoice ? true : undefined}
              onChange={() => choose(t.key)}
            />
            {t.name}
          </label>
        ))}
        <label className="add-task__option">
          <input
            ref={missing.length === 0 ? firstRadio : undefined}
            type="radio"
            name="oppgave"
            value={CUSTOM}
            checked={choice === CUSTOM}
            onChange={() => choose(CUSTOM)}
          />
          Egen oppgave
        </label>
      </fieldset>
      {noChoice && (
        <p id={ids.error} className="auth-form__error" role="alert">
          {TASK_MESSAGES.chooseOne}
        </p>
      )}
      {choice === CUSTOM && (
        <div className="text-field">
          <label className="text-field__label" htmlFor="ny-oppgave-navn">
            Navn på oppgaven
          </label>
          <input
            id="ny-oppgave-navn"
            ref={nameInput}
            className="text-field__input"
            type="text"
            autoComplete="off"
            value={name}
            aria-invalid={nameError ? true : undefined}
            aria-describedby={nameError ? ids.nameError : undefined}
            onChange={(e) => {
              edited();
              setName(e.target.value);
            }}
          />
          {nameError && (
            <p id={ids.nameError} className="text-field__error" role="alert">
              {nameError}
            </p>
          )}
        </div>
      )}
      {choice !== null && (
        <div className="add-task__settings">
          <div className="task-setup__choices" role="radiogroup" aria-label="Må eller bør">
            {(['must', 'should'] as const).map((value) => (
              <label key={value} className={`task-setup__pill task-setup__pill--${value}`}>
                <input
                  type="radio"
                  name="klassifisering"
                  value={value}
                  checked={draft.classification === value}
                  onChange={() => {
                    edited();
                    setDraft((d) => ({ ...d, classification: value }));
                  }}
                />
                {CLASSIFICATION_LABELS[value]}
              </label>
            ))}
          </div>
          <label className="task-setup__frequency">
            <span>Hvor ofte</span>
            <select
              className="task-setup__select"
              value={draft.frequency}
              onChange={(e) => {
                edited();
                setDraft((d) => ({ ...d, frequency: Number(e.target.value) as Frequency }));
              }}
            >
              {frequencies.map((days) => (
                <option key={days} value={days}>
                  {FREQUENCY_LABELS[days]}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}
      {formError && (
        <p className="auth-form__error" role="alert">
          {formError}
        </p>
      )}
      <PrimaryButton type="submit" pending={add.isPending}>
        {error ? 'Prøv igjen' : 'Legg til'}
      </PrimaryButton>
    </form>
  );
}

/**
 * The inline message for a failed add. A 403 shows none: the global handler refetches and the
 * guards route. A 409 or 422 shows the server's reason; anything else the generic message.
 */
function submitError(error: Error | null): string | null {
  if (!error) return null;
  if (error instanceof ApiError) {
    if (error.status === 403) return null;
    return error.message;
  }
  return TASK_MESSAGES.addFailed;
}

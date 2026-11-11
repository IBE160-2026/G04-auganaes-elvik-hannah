// Story 2.1 (FR-4, FR-8, AD-6): Task Setup after Create Home. The user reviews the catalog's
// recommended tasks, adjusts Må/Bør and the interval, unticks what does not fit, and saves them
// all in one request. Who may do this is the server's can_set_up_tasks; whether the Home already
// has Tasks is its has_tasks. Decision 8: never a dead end, so «Medlemmer og invitasjon» and
// «Logg ut» are at the bottom. A 403 shows no inline error: the global handler refetches and the
// guards route; a 409 shows the server's reason and refetches, and the guard sends the user on.
// Story 2.2 (decision 12): success and the has_tasks guard both go to this Home's /hjem/<id>,
// never to "/", which would open the most recently used Home instead.
import { useId, useRef, useState, type FormEvent } from 'react';
import { flushSync } from 'react-dom';
import { Link, Navigate, useNavigate, useParams } from 'react-router';
import { ApiError } from '../api/errors';
import type { Home } from '../api/homes';
import { useHomes, useSetUpTasks, useSignOut, useTaskTypes } from '../api/queries';
import {
  CLASSIFICATION_LABELS,
  FREQUENCY_LABELS,
  TASK_MESSAGES,
  type Classification,
  type Frequency,
  type TaskChoice,
  type TaskTypes,
} from '../api/tasks';
import { PendingNotice } from '../components/PendingNotice';
import { PrimaryButton } from '../components/PrimaryButton';
import { HomesLoadError } from './HomesLoadError';
import './AuthForm.css';
import './TaskSetup.css';

export function TaskSetup() {
  const { homeId } = useParams();
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  // A failed background refetch keeps the cached data; only a load with nothing to show is an error.
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  const home = homes.data.homes.find((h) => h.id === homeId);
  // Not theirs (or a typo): to "/". Not theirs to set up (a Tenant), or set up already: to the
  // Home's own Task Overview.
  if (!home) return <Navigate to="/" replace />;
  if (!home.can_set_up_tasks || home.has_tasks) return <Navigate to={`/hjem/${home.id}`} replace />;

  return <SetupPage key={home.id} home={home} />;
}

// Rendered only once the Home is found and may be set up.
function SetupPage({ home }: { home: Home }) {
  const taskTypes = useTaskTypes();
  const signOut = useSignOut();

  return (
    <div className="task-setup">
      {/* A Landlord who just left a Household may land here first (Story 1.8). */}
      <PendingNotice className="task-setup__notice" />
      <h1 className="task-setup__title">Sett opp oppgaver</h1>
      <p className="task-setup__lead">
        Dette er oppgavene vi anbefaler for «{home.name}». Velg om de må eller bør gjøres og hvor ofte, og
        fjern haken for det som ikke passer.
      </p>
      {taskTypes.data ? (
        <SetupForm home={home} catalog={taskTypes.data} />
      ) : taskTypes.isError ? (
        <>
          <p className="auth-form__error" role="alert">
            {TASK_MESSAGES.typesLoadFailed}
          </p>
          <PrimaryButton onClick={() => void taskTypes.refetch()}>Prøv igjen</PrimaryButton>
        </>
      ) : (
        // No role="status": the Homes loading above already uses it.
        <p className="task-setup__note">Henter forslag …</p>
      )}
      <div className="task-setup__exits">
        <Link to={`/hjem/${home.id}/medlemmer`} className="task-setup__link">
          Medlemmer og invitasjon
        </Link>
        <button
          type="button"
          className="task-setup__secondary"
          aria-busy={signOut.isPending || undefined}
          onClick={() => signOut.mutate()}
        >
          Logg ut
        </button>
      </div>
    </div>
  );
}

type Row = { included: boolean; classification: Classification; frequency: Frequency };

function SetupForm({ home, catalog }: { home: Home; catalog: TaskTypes }) {
  const setUp = useSetUpTasks(home.id);
  const navigate = useNavigate();
  const errorId = useId();
  const firstCheckbox = useRef<HTMLInputElement>(null);
  // The user's draft, started from the catalog's recommendations.
  const [rows, setRows] = useState<Record<string, Row>>(() =>
    Object.fromEntries(
      catalog.task_types.map((t) => [
        t.key,
        { included: true, classification: t.classification, frequency: t.frequency_days },
      ]),
    ),
  );
  const [noneChosen, setNoneChosen] = useState(false);

  function update(key: string, change: Partial<Row>) {
    setRows((old) => ({ ...old, [key]: { ...old[key], ...change } }));
    if (change.included) setNoneChosen(false);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (setUp.isPending) return;
    const chosen: TaskChoice[] = catalog.task_types
      .filter((t) => rows[t.key].included)
      .map((t) => ({
        task_type: t.key,
        classification: rows[t.key].classification,
        frequency_days: rows[t.key].frequency,
      }));
    if (chosen.length === 0) {
      // Render the message first, so it is announced together with the focus move.
      flushSync(() => setNoneChosen(true));
      firstCheckbox.current?.focus();
      return;
    }
    setNoneChosen(false);
    setUp.mutate(chosen, { onSuccess: () => navigate(`/hjem/${home.id}`, { replace: true }) });
  }

  const error = submitError(setUp.error);

  return (
    <form className="task-setup__form" onSubmit={handleSubmit} noValidate>
      <ul className="task-setup__list">
        {catalog.task_types.map((t, index) => {
          const row = rows[t.key];
          const radioName = `klassifisering-${t.key}`;
          return (
            <li key={t.key}>
              <fieldset className={`task-setup__row${row.included ? '' : ' task-setup__row--off'}`}>
                <legend className="task-setup__name">{t.name}</legend>
                <label className="task-setup__check">
                  <input
                    ref={index === 0 ? firstCheckbox : undefined}
                    type="checkbox"
                    checked={row.included}
                    onChange={(e) => update(t.key, { included: e.target.checked })}
                    aria-invalid={index === 0 && noneChosen ? true : undefined}
                    aria-describedby={index === 0 && noneChosen ? errorId : undefined}
                  />
                  Ta med
                </label>
                <div className="task-setup__choices" role="radiogroup" aria-label={`Må eller bør: ${t.name}`}>
                  {(['must', 'should'] as const).map((value) => (
                    <label key={value} className={`task-setup__pill task-setup__pill--${value}`}>
                      <input
                        type="radio"
                        name={radioName}
                        value={value}
                        checked={row.classification === value}
                        onChange={() => update(t.key, { classification: value })}
                      />
                      {CLASSIFICATION_LABELS[value]}
                    </label>
                  ))}
                </div>
                <label className="task-setup__frequency">
                  <span>Hvor ofte</span>
                  <select
                    className="task-setup__select"
                    value={row.frequency}
                    onChange={(e) => update(t.key, { frequency: Number(e.target.value) as Frequency })}
                  >
                    {catalog.frequencies.map((days) => (
                      <option key={days} value={days}>
                        {FREQUENCY_LABELS[days]}
                      </option>
                    ))}
                  </select>
                </label>
              </fieldset>
            </li>
          );
        })}
      </ul>
      {noneChosen && (
        <p id={errorId} className="auth-form__error" role="alert">
          {TASK_MESSAGES.noneChosen}
        </p>
      )}
      {error && (
        <p className="auth-form__error" role="alert">
          {error}
        </p>
      )}
      <PrimaryButton type="submit" pending={setUp.isPending}>
        {error ? 'Prøv igjen' : 'Lagre oppgavene'}
      </PrimaryButton>
    </form>
  );
}

/**
 * The inline message for a failed save. A 403 (no longer allowed) shows none: the global handler
 * refetches and the guards route. A 409 (set up meanwhile) shows the server's reason, so a failed
 * refetch never leaves the user on a silent form; a successful one sends them to "/".
 */
function submitError(error: Error | null): string | null {
  if (!error) return null;
  if (error instanceof ApiError) {
    if (error.status === 403) return null;
    return error.message;
  }
  return TASK_MESSAGES.setupFailed;
}

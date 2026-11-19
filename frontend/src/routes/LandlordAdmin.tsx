// Story 3.4 (FR-12, UX-DR12): Landlord Home Admin, first built here as a shell with the
// broadcast composer. Story 3.5 (FR-13) adds the reminder cadence: a radio group of whole-day
// options saved with «Lagre», confirmed in a polite live region, a failed save shown inline with
// «Prøv igjen» at the action (UX-DR30). Whether the caller may send is the
// server's can_broadcast, never decided here, so a Tenant or Household Member is sent back to the
// Home. A send confirms with a count in an aria-live="polite" region and names nobody. A failed
// send keeps the text and offers «Prøv igjen». A 403 shows no inline error: the global handler in
// createQueryClient refetches the Homes and the guard routes.
import { useState, type FormEvent } from 'react';
import { Link, Navigate, useParams } from 'react-router';
import { ApiError } from '../api/errors';
import {
  BROADCAST_MAX,
  sentNotice,
  validateBroadcast,
} from '../api/broadcast';
import type { Home } from '../api/homes';
import { CADENCE_MESSAGES, CADENCE_OPTIONS, type CadenceDays } from '../api/cadence';
import { useHomes, useSaveCadence, useSendBroadcast } from '../api/queries';
import { PrimaryButton } from '../components/PrimaryButton';
import { HomesLoadError } from './HomesLoadError';
import './AuthForm.css';
import './LandlordAdmin.css';

export function LandlordAdmin() {
  const { homeId } = useParams();
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  const home = homes.data.homes.find((h) => h.id === homeId);
  if (!home) return <Navigate to="/" replace />;
  if (!home.can_broadcast) return <Navigate to={`/hjem/${home.id}`} replace />;

  return (
    <div className="landlord-admin">
      <h1 className="landlord-admin__title">Administrer hjemmet</h1>
      <p className="landlord-admin__lead">{home.name}</p>
      <Composer key={home.id} home={home} />
      {home.can_set_cadence && <CadenceSection key={home.id} home={home} />}
      <Link to={`/hjem/${home.id}`} className="landlord-admin__link">
        Tilbake til hjemmet
      </Link>
    </div>
  );
}

function Composer({ home }: { home: Home }) {
  const send = useSendBroadcast(home.id);
  const [text, setText] = useState('');
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [notice, setNotice] = useState('');

  // One path for «Send melding» and «Prøv igjen»: both validate, and both confirm the same way.
  function attempt() {
    const problem = validateBroadcast(text);
    setFieldError(problem);
    setNotice('');
    if (problem) return;
    send.mutate(text.trim(), {
      onSuccess: (result) => {
        setNotice(sentNotice(result));
        // Nobody was reached: the text stays so the Landlord can try again.
        if (result.recipients > 0) setText('');
      },
    });
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    attempt();
  }

  const failure =
    send.error instanceof ApiError && send.error.status === 403
      ? null
      : (send.error?.message ?? null);

  return (
    <form className="landlord-admin__section" onSubmit={submit} noValidate>
      <h2 className="landlord-admin__subtitle">Send melding til leietakerne</h2>
      <label className="landlord-admin__label" htmlFor="broadcast-text">
        Melding
      </label>
      <textarea
        id="broadcast-text"
        className="landlord-admin__input"
        rows={4}
        value={text}
        onChange={(event) => setText(event.target.value)}
        aria-invalid={fieldError ? true : undefined}
        aria-describedby={fieldError ? 'broadcast-error broadcast-count' : 'broadcast-count'}
      />
      <p id="broadcast-count" className="landlord-admin__note">
        {[...text].length} av {BROADCAST_MAX} tegn
      </p>
      {fieldError && (
        <p id="broadcast-error" className="auth-form__error">
          {fieldError}
        </p>
      )}
      <PrimaryButton type="submit" pending={send.isPending}>
        Send melding
      </PrimaryButton>
      {failure && (
        <>
          <p className="auth-form__error" role="alert">
            {failure}
          </p>
          {/* Nothing to retry when the Home has no Tenants (409): the message would be refused again. */}
          {!(send.error instanceof ApiError && send.error.status === 409) && (
            <button type="button" className="landlord-admin__retry" onClick={attempt}>
              Prøv igjen
            </button>
          )}
        </>
      )}
      {/* Always in the DOM, so the confirmation is announced when it arrives. */}
      <p className="landlord-admin__note" aria-live="polite">
        {notice}
      </p>
    </form>
  );
}

function CadenceSection({ home }: { home: Home }) {
  const save = useSaveCadence(home.id);
  // Seeded once from the server's value; a change made elsewhere shows after the next visit.
  const [days, setDays] = useState<CadenceDays>(home.notification_cadence_days as CadenceDays);
  const [notice, setNotice] = useState('');

  function attempt() {
    setNotice('');
    save.mutate(days, { onSuccess: () => setNotice(CADENCE_MESSAGES.saved) });
  }

  const failure =
    save.error instanceof ApiError && save.error.status === 403 ? null : (save.error?.message ?? null);

  return (
    <form
      className="landlord-admin__section"
      onSubmit={(event) => {
        event.preventDefault();
        attempt();
      }}
    >
      <h2 className="landlord-admin__subtitle">Påminnelser til leietakerne</h2>
      <fieldset className="landlord-admin__fieldset">
        <legend className="landlord-admin__label">
          Hvor ofte skal leietakerne minnes på Må-oppgaver?
        </legend>
        {CADENCE_OPTIONS.map((option) => (
          <label key={option.days} className="landlord-admin__option">
            <input
              type="radio"
              name="cadence"
              value={option.days}
              checked={days === option.days}
              onChange={() => {
                setDays(option.days);
                setNotice('');
                // An old error belongs to the value that failed, not to this choice.
                save.reset();
              }}
            />
            {option.label}
          </label>
        ))}
      </fieldset>
      <p className="landlord-admin__note">
        Gjelder bare leietakere og Må-oppgaver. Første påminnelse kommer på fristdagen. Det endrer
        ikke hvor ofte oppgaven skal gjøres.
      </p>
      <PrimaryButton type="submit" pending={save.isPending}>
        Lagre
      </PrimaryButton>
      {failure && (
        <>
          <p className="auth-form__error" role="alert">
            {failure}
          </p>
          <button type="button" className="landlord-admin__retry" onClick={attempt}>
            Prøv igjen
          </button>
        </>
      )}
      <p className="landlord-admin__note" aria-live="polite">
        {notice}
      </p>
    </form>
  );
}

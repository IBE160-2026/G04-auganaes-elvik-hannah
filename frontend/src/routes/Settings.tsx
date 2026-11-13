// Story 2.2 (decision 4): Settings/Profile at /innstillinger. The user's name and e-mail, «Dine
// hjem» to switch between Homes (each with «Medlemmer», and «Sett opp oppgaver» while it has no
// Tasks and the user may set them up), «Opprett nytt hjem» when the server's allowed_types offers
// something, and «Logg ut». «Bytt hjem» on the Task Overview lands on #dine-hjem.
// Story 3.1 (FR-10, UX-DR31): «Varsler» shows the browser's push permission plainly and turns push
// on for this device with one tap; with permission already granted the device is registered
// silently, so a user who signs in on a browser that allowed push is not left without a row.
import { useEffect, useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router';
import { ROLE_LABELS, type Home } from '../api/homes';
import { PUSH_MESSAGES, readPushStatus, type PushStatus } from '../api/push';
import { useEnablePush, useHomes, useMe, useRegisterDevice, useSignOut } from '../api/queries';
import { PrimaryButton } from '../components/PrimaryButton';
import { HomesLoadError } from './HomesLoadError';
import { useFocusOnMount } from './useFocusOnMount';
import './Settings.css';

export const HOMES_ANCHOR = 'dine-hjem';

export function Settings() {
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  if (homes.data.homes.length === 0) return <Navigate to="/nytt-hjem" replace />;

  return <SettingsPage homes={homes.data.homes} canCreate={homes.data.allowed_types.length > 0} />;
}

function SettingsPage({ homes, canCreate }: { homes: readonly Home[]; canCreate: boolean }) {
  const me = useMe();
  const signOut = useSignOut();
  // Decision 14: the page heading, or «Dine hjem» when «Bytt hjem» sent the user here.
  const toHomes = useLocation().hash === `#${HOMES_ANCHOR}`;
  const titleRef = useFocusOnMount<HTMLHeadingElement>();
  const homesRef = useFocusOnMount<HTMLHeadingElement>();

  return (
    <div className="settings">
      <h1 ref={toHomes ? undefined : titleRef} tabIndex={-1} className="settings__title">
        Innstillinger
      </h1>
      <section className="settings__section" aria-labelledby="settings-profile">
        <h2 id="settings-profile" className="settings__subtitle">
          Profil
        </h2>
        <dl className="settings__facts">
          <div>
            <dt>Navn</dt>
            <dd>{me.data?.name}</dd>
          </div>
          <div>
            <dt>E-post</dt>
            <dd>{me.data?.email}</dd>
          </div>
        </dl>
      </section>
      <section className="settings__section" aria-labelledby={HOMES_ANCHOR}>
        <h2 id={HOMES_ANCHOR} ref={toHomes ? homesRef : undefined} tabIndex={-1} className="settings__subtitle">
          Dine hjem
        </h2>
        <ul className="settings__homes">
          {homes.map((home) => (
            <li key={home.id} className="settings__home">
              <span className="settings__home-name">
                <Link to={`/hjem/${home.id}`} className="settings__link">
                  {home.name}
                </Link>
                <span className="settings__meta">{ROLE_LABELS[home.role]}</span>
              </span>
              <span className="settings__home-links">
                <Link
                  to={`/hjem/${home.id}/medlemmer`}
                  className="settings__link"
                  aria-label={`Medlemmer og invitasjon for ${home.name}`}
                >
                  Medlemmer
                </Link>
                {home.can_set_up_tasks && !home.has_tasks && (
                  <Link
                    to={`/hjem/${home.id}/oppgaveoppsett`}
                    className="settings__link"
                    aria-label={`Sett opp oppgaver for ${home.name}`}
                  >
                    Sett opp oppgaver
                  </Link>
                )}
              </span>
            </li>
          ))}
        </ul>
        {canCreate && (
          <Link to="/nytt-hjem" className="settings__link">
            Opprett nytt hjem
          </Link>
        )}
      </section>
      <PushSection />
      <PrimaryButton onClick={() => signOut.mutate()} pending={signOut.isPending}>
        Logg ut
      </PrimaryButton>
    </div>
  );
}

function PushSection() {
  const [status, setStatus] = useState<PushStatus | null>(null);
  const enable = useEnablePush();
  const register = useRegisterDevice();
  const { mutate: registerSilently } = register;

  useEffect(() => {
    let current = true;
    void readPushStatus().then((value) => {
      if (!current) return;
      setStatus(value);
      // Only on opening the page: a tap on «Slå på varsler» registers the device itself.
      if (value === 'granted') registerSilently();
    });
    return () => {
      current = false;
    };
  }, [registerSilently]);

  const failed = enable.isError || register.isError;

  function turnOn() {
    // A failed silent registration must not keep its error after a retry that works.
    register.reset();
    enable.mutate(undefined, { onSettled: () => void readPushStatus().then(setStatus) });
  }

  return (
    <section className="settings__section" aria-labelledby="settings-push">
      <h2 id="settings-push" className="settings__subtitle">
        {PUSH_MESSAGES.title}
      </h2>
      {status === null ? (
        <p role="status">Laster …</p>
      ) : (
        <p aria-live="polite">{PUSH_MESSAGES[status]}</p>
      )}
      {failed && (
        <p className="settings__error" role="alert">
          {PUSH_MESSAGES.failed}
        </p>
      )}
      {(status === 'default' || (failed && status === 'granted')) && (
        <PrimaryButton onClick={turnOn} pending={enable.isPending}>
          {failed ? PUSH_MESSAGES.retry : PUSH_MESSAGES.enable}
        </PrimaryButton>
      )}
    </section>
  );
}

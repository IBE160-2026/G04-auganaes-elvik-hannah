// Story 1.4 (FR-2, team decision 4): "Medlemmer og invitasjon" for one Home. A Household Member
// or the Landlord makes an invite link here; for a Tenant the control is absent, not disabled.
// Whether the caller may invite is the server's can_invite, never decided here.
// Story 1.5 (FR-3, SM-6): every Member sees every Member of the Home and their Role, above the
// invite control. A failed members load is shown at the list and never hides the invite control.
import { useState } from 'react';
import { Link, Navigate, useParams } from 'react-router';
import { MEMBER_MESSAGES, ROLE_LABELS, type Home } from '../api/homes';
import { INVITE_MESSAGES, inviteUrl, type Invite } from '../api/invites';
import { useCreateInvite, useHomes, useMembers } from '../api/queries';
import { PrimaryButton } from '../components/PrimaryButton';
import { HomesLoadError } from './HomesLoadError';
import './AuthForm.css';
import './MembersPage.css';

const EXPIRY_FORMAT = new Intl.DateTimeFormat('nb-NO', {
  day: 'numeric',
  month: 'long',
  hour: '2-digit',
  minute: '2-digit',
});

export function MembersPage() {
  const { homeId } = useParams();
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  // A failed background refetch keeps the cached data; only a load with nothing to show is an error.
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  const home = homes.data.homes.find((h) => h.id === homeId);
  // Only a loaded list without this Home sends the user away (not theirs, or a typo).
  if (!home) return <Navigate to="/" replace />;

  return (
    <div className="members-page">
      <h1 className="members-page__title">Medlemmer og invitasjon</h1>
      <p className="members-page__lead">{home.name}</p>
      <MembersList key={home.id} homeId={home.id} />
      {home.can_invite ? (
        <InviteControl key={home.id} home={home} />
      ) : (
        <p className="members-page__note">Det er utleieren som inviterer nye leietakere.</p>
      )}
      <Link to="/" className="members-page__link">
        Tilbake til hjemmet
      </Link>
    </div>
  );
}

// Rendered only once the Home is found, so a foreign or mistyped id is never fetched.
function MembersList({ homeId }: { homeId: string }) {
  const members = useMembers(homeId);

  return (
    <section className="members-page__section" aria-labelledby="members-page-members">
      <h2 id="members-page-members" className="members-page__subtitle">
        Medlemmer
      </h2>
      {members.data ? (
        <ul className="members-page__list">
          {members.data.map((member) => (
            <li key={member.user_id} className="members-page__member">
              <span className="members-page__name">
                {member.name}
                {member.is_you && ' (deg)'}
              </span>
              <span className="members-page__visually-hidden">, </span>
              <span className="members-page__role">{ROLE_LABELS[member.role]}</span>
            </li>
          ))}
        </ul>
      ) : members.isError ? (
        <>
          <p className="auth-form__error" role="alert">
            {MEMBER_MESSAGES.loadFailed}
          </p>
          <button
            type="button"
            className="members-page__secondary"
            aria-label="Prøv å hente medlemmene igjen"
            onClick={() => void members.refetch()}
          >
            Prøv igjen
          </button>
        </>
      ) : (
        // No role="status": the Homes loading above already uses it.
        <p className="members-page__note">Henter medlemmer …</p>
      )}
    </section>
  );
}

function InviteControl({ home }: { home: Home }) {
  const createInvite = useCreateInvite(home.id);
  const [invite, setInvite] = useState<Invite | null>(null);
  const [copied, setCopied] = useState<'yes' | 'failed' | null>(null);

  function generate() {
    setCopied(null);
    createInvite.mutate(undefined, { onSuccess: setInvite });
  }

  async function copy(url: string) {
    try {
      await navigator.clipboard.writeText(url);
      setCopied('yes');
    } catch {
      setCopied('failed');
    }
  }

  const url = invite ? inviteUrl(invite.token) : null;
  const who = home.type === 'household' ? 'noen du bor med' : 'en ny leietaker';

  return (
    <section className="members-page__section" aria-labelledby="members-page-invite">
      <h2 id="members-page-invite" className="members-page__subtitle">
        Inviter
      </h2>
      <p className="members-page__note">Lag en lenke og send den til {who}.</p>
      {invite && url && (
        <div className="members-page__invite">
          <label className="members-page__label" htmlFor="members-page-link">
            Invitasjonslenke
          </label>
          <input id="members-page-link" className="members-page__input" value={url} readOnly />
          <p className="members-page__note">
            Kan brukes én gang, gyldig til {EXPIRY_FORMAT.format(new Date(invite.expires_at))}.
          </p>
          <button type="button" className="members-page__secondary" onClick={() => void copy(url)}>
            Kopier lenke
          </button>
          <p className="members-page__note" role="status">
            {copied === 'yes' && 'Lenken er kopiert.'}
            {copied === 'failed' && 'Fikk ikke kopiert. Marker lenken og kopier den selv.'}
          </p>
        </div>
      )}
      {createInvite.isError && (
        <p className="auth-form__error" role="alert">
          {INVITE_MESSAGES.createFailed}
        </p>
      )}
      <PrimaryButton onClick={generate} pending={createInvite.isPending}>
        {createInvite.isError ? 'Prøv igjen' : invite ? 'Lag ny lenke' : 'Lag invitasjonslenke'}
      </PrimaryButton>
    </section>
  );
}

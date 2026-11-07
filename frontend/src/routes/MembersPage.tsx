// Story 1.4 (FR-2, team decision 4): "Medlemmer og invitasjon" for one Home. A Household Member
// or the Landlord makes an invite link here; for a Tenant the control is absent, not disabled.
// Whether the caller may invite is the server's can_invite, never decided here. Story 1.5 adds
// the members list to this page.
import { useState } from 'react';
import { Link, Navigate, useParams } from 'react-router';
import type { Home } from '../api/homes';
import { INVITE_MESSAGES, inviteUrl, type Invite } from '../api/invites';
import { useCreateInvite, useHomes } from '../api/queries';
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

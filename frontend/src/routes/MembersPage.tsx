// Story 1.4 (FR-2, team decision 4): "Medlemmer og invitasjon" for one Home. A Household Member
// or the Landlord makes an invite link here; for a Tenant the control is absent, not disabled.
// Whether the caller may invite is the server's can_invite, never decided here.
// Story 1.5 (FR-3, SM-6): every Member sees every Member of the Home and their Role, above the
// invite control. A failed members load is shown at the list and never hides the invite control.
// Story 1.8 (FR-23): «Forlat hjemmet» when the server's can_leave says so, and «Fjern» on each
// row whose can_remove is true (a Landlord, on a Tenant). Both confirm inline. A 403 shows no
// inline error: the global handler in createQueryClient refetches and the guards route.
// Story 2.2: «Tilbake til hjemmet» goes to this Home's Task Overview.
import { useRef, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router';
import { ApiError } from '../api/errors';
import { MEMBER_MESSAGES, ROLE_LABELS, type Home, type Member } from '../api/homes';
import { INVITE_MESSAGES, inviteUrl, type Invite } from '../api/invites';
import { useCreateInvite, useHomes, useLeaveHome, useMembers, useRemoveMember } from '../api/queries';
import { ConfirmAction } from '../components/ConfirmAction';
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
      <MembersList key={home.id} home={home} />
      {home.can_invite ? (
        <InviteControl key={home.id} home={home} />
      ) : (
        <p className="members-page__note">Det er utleieren som inviterer nye leietakere.</p>
      )}
      {home.can_leave && <LeaveControl key={home.id} home={home} />}
      <Link to={`/hjem/${home.id}`} className="members-page__link">
        Tilbake til hjemmet
      </Link>
    </div>
  );
}

/** A failure worth showing inline: a 403 is handled by the global refetch instead. */
function inlineError(error: Error | null, message: string): string | null {
  if (!error || (error instanceof ApiError && error.status === 403)) return null;
  return message;
}

// Rendered only once the Home is found, so a foreign or mistyped id is never fetched.
function MembersList({ home }: { home: Home }) {
  const members = useMembers(home.id);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [removed, setRemoved] = useState<string | null>(null);

  // The removed row and its button are gone: focus goes to the heading.
  function onRemoved(member: Member) {
    setRemoved(MEMBER_MESSAGES.removedNotice(member.name));
    headingRef.current?.focus();
  }

  return (
    <section className="members-page__section" aria-labelledby="members-page-members">
      <h2 id="members-page-members" ref={headingRef} tabIndex={-1} className="members-page__subtitle">
        Medlemmer
      </h2>
      {members.data ? (
        <ul className="members-page__list">
          {members.data.map((member) => (
            <li key={member.user_id} className="members-page__member">
              <span className="members-page__person">
                <span className="members-page__name">
                  {member.name}
                  {member.is_you && ' (deg)'}
                </span>
                <span className="members-page__visually-hidden">, </span>
                <span className="members-page__role">{ROLE_LABELS[member.role]}</span>
              </span>
              {member.can_remove && (
                <RemoveControl
                  home={home}
                  member={member}
                  onRemoved={onRemoved}
                  onGone={() => headingRef.current?.focus()}
                />
              )}
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
      {/* Always in the DOM, so the text is announced when it arrives. No role="status" either. */}
      <p className="members-page__note" aria-live="polite">
        {removed}
      </p>
    </section>
  );
}

/**
 * One Tenant row's «Fjern», with its own mutation, so rows never share or reset each other's
 * state. mutateAsync, not mutate's callbacks: the row unmounts once the refetch drops it, and
 * the promise still settles then.
 */
function RemoveControl({
  home,
  member,
  onRemoved,
  onGone,
}: {
  home: Home;
  member: Member;
  onRemoved: (member: Member) => void;
  onGone: () => void;
}) {
  const remove = useRemoveMember(home.id);

  function confirm(close: () => void) {
    remove.mutateAsync(member.user_id).then(
      () => onRemoved(member),
      (error: unknown) => {
        // Gone already (left meanwhile): fold the confirmation so no second DELETE can be sent;
        // the row disappears on the refetch, so focus goes to the heading.
        if (error instanceof ApiError && error.status === 403) {
          close();
          onGone();
        }
      },
    );
  }

  return (
    <ConfirmAction
      label="Fjern"
      ariaLabel={`Fjern ${member.name}`}
      explanation={`${member.name} mister tilgangen til «${home.name}».`}
      confirmLabel={`Ja, fjern ${member.name}`}
      onConfirm={confirm}
      onCancel={() => remove.reset()}
      pending={remove.isPending}
      error={inlineError(remove.error, MEMBER_MESSAGES.removeFailed)}
    />
  );
}

function LeaveControl({ home }: { home: Home }) {
  const leave = useLeaveHome(home);

  return (
    <div className="members-page__leave">
      <ConfirmAction
        label="Forlat hjemmet"
        explanation={`Du mister tilgangen til «${home.name}». Oppgavene du har gjort, blir stående.`}
        confirmLabel="Ja, forlat hjemmet"
        onConfirm={(close) =>
          leave.mutate(undefined, {
            // Refused: fold the confirmation; the refetch then sends the user away.
            onError: (error) => {
              if (error instanceof ApiError && error.status === 403) close();
            },
          })
        }
        onCancel={() => leave.reset()}
        pending={leave.isPending}
        error={inlineError(leave.error, MEMBER_MESSAGES.leaveFailed)}
      />
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

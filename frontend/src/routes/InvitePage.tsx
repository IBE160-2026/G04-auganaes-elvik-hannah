// Story 1.4 (FR-2, UJ-1, UJ-2): what someone sees when they open an invite link. Public: a
// signed-out visitor sees the Home and can register or sign in; a signed-in one can join with
// one tap, or is told why not. Whether they can join comes from the server (viewer), so the
// one-Home rule is never copied here. An invalid link shows a message, never a 404.
import { Link, useLocation, useNavigate, useParams } from 'react-router';
import { ROLE_LABELS } from '../api/homes';
import { INVITE_MESSAGES, InviteError, invalidInviteMessage, validInviteToken, type InvitePreview } from '../api/invites';
import { useAcceptInvite, useInvite } from '../api/queries';
import { useSession } from '../api/session';
import { PrimaryButton } from '../components/PrimaryButton';
import './AuthForm.css';
import './InvitePage.css';

export function InvitePage() {
  const token = validInviteToken(useParams().token);
  if (!token) return <InvalidInvite homeType={null} />;
  // Keyed, so a different token never shows the previous one's state.
  return <ValidTokenInvite key={token} token={token} />;
}

function InvalidInvite({ homeType }: { homeType: InvitePreview['home_type'] }) {
  const session = useSession();
  return (
    <div className="auth-page">
      <h1 className="auth-page__title">Invitasjonen gjelder ikke lenger</h1>
      <p className="invite-page__message">{invalidInviteMessage(homeType)}</p>
      {session && (
        <Link to="/" className="invite-page__link">
          Gå til forsiden
        </Link>
      )}
    </div>
  );
}

function ValidTokenInvite({ token }: { token: string }) {
  const session = useSession();
  const invite = useInvite(token);
  const accept = useAcceptInvite(token);
  const navigate = useNavigate();
  // Set by Register after an account was made through this link.
  const justRegistered = (useLocation().state as { justRegistered?: boolean } | null)?.justRegistered === true;

  if (invite.isPending) return <p role="status">Laster …</p>;
  if (!invite.data) {
    return (
      <div className="auth-page">
        <p className="auth-form__error" role="alert">
          {INVITE_MESSAGES.loadFailed}
        </p>
        <PrimaryButton onClick={() => void invite.refetch()}>Prøv igjen</PrimaryButton>
      </div>
    );
  }

  const preview = invite.data;
  if (preview.status === 'invalid' || !preview.home_name || !preview.role) {
    return <InvalidInvite homeType={preview.home_type} />;
  }
  const homeName = preview.home_name;
  const role = ROLE_LABELS[preview.role].toLowerCase();
  const title = preview.home_type === 'household' ? `Bli med i «${homeName}»` : `Invitasjon til «${homeName}»`;

  if (!session || !preview.viewer) {
    return (
      <div className="auth-page">
        <h1 className="auth-page__title">{title}</h1>
        <p className="invite-page__message">
          Du er invitert til «{homeName}» som {role}. Opprett en konto for å bli med, eller logg inn hvis du
          allerede har en.
        </p>
        <PrimaryButton onClick={() => navigate(`/registrer?invitasjon=${token}`)}>Opprett konto og bli med</PrimaryButton>
        <Link to={`/logg-inn?invitasjon=${token}`} className="invite-page__link">
          Logg inn
        </Link>
      </div>
    );
  }

  if (preview.viewer === 'already_member' && justRegistered) {
    return (
      <div className="auth-page">
        <h1 className="auth-page__title">{homeName}</h1>
        <p className="invite-page__message">Velkommen! Du er nå med i «{homeName}».</p>
        <Link to="/" className="invite-page__link">
          Gå til hjemmet
        </Link>
      </div>
    );
  }

  if (preview.viewer === 'already_member') {
    return (
      <div className="auth-page">
        <h1 className="auth-page__title">{homeName}</h1>
        <p className="invite-page__message">Du er allerede med i «{homeName}».</p>
        <Link to="/" className="invite-page__link">
          Gå til forsiden
        </Link>
      </div>
    );
  }

  if (preview.viewer === 'in_other_home') {
    return (
      <div className="auth-page">
        <h1 className="auth-page__title">Invitasjon til «{homeName}»</h1>
        <p className="invite-page__message">
          Du er allerede med i «{preview.other_home_name}». Du kan bare være med i ett hjem om gangen.
        </p>
        {/* "/" shows the newest Home, which may not be the one named above (Epic 1 retro, R7). */}
        <Link to="/" className="invite-page__link">
          Gå til forsiden
        </Link>
      </div>
    );
  }

  function join() {
    accept.mutate(undefined, {
      onSuccess: () => navigate('/', { replace: true }),
      // The link or the user changed meanwhile: show the server's reason, then the new state.
      onError: () => void invite.refetch(),
    });
  }

  const joinError = accept.error instanceof InviteError ? accept.error.message : INVITE_MESSAGES.unknown;

  return (
    <div className="auth-page">
      <h1 className="auth-page__title">{title}</h1>
      <p className="invite-page__message">
        Du er invitert til «{homeName}» som {role}.
      </p>
      {accept.isError && (
        <p className="auth-form__error" role="alert">
          {joinError}
        </p>
      )}
      <PrimaryButton onClick={join} pending={accept.isPending}>
        Bli med i «{homeName}»
      </PrimaryButton>
    </div>
  );
}

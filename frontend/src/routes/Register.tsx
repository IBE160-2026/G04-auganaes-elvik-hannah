// Story 1.2 (FR-1): create an account with email, display name and password.
// Story 1.4 (FR-2): with ?invitasjon=<token>, the account joins that Home in the same request,
// and the user goes back to the invite page (never straight to "/"), which shows the result.
import { useRef, useState, type FormEvent } from 'react';
import { flushSync } from 'react-dom';
import { Link, Navigate, useSearchParams } from 'react-router';
import { AuthError, MESSAGES, PASSWORD_MIN, validateRegister, type FieldErrors } from '../api/auth';
import { validInviteToken } from '../api/invites';
import { useRegister } from '../api/queries';
import { useSession } from '../api/session';
import { PrimaryButton } from '../components/PrimaryButton';
import { TextField } from '../components/TextField';
import { focusFirstInvalid } from './formFocus';
import './AuthForm.css';

export function Register() {
  const session = useSession();
  const register = useRegister();
  const formRef = useRef<HTMLFormElement>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [emailTaken, setEmailTaken] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [searchParams] = useSearchParams();
  const inviteToken = validInviteToken(searchParams.get('invitasjon'));
  const signInPath = inviteToken ? `/logg-inn?invitasjon=${inviteToken}` : '/logg-inn';

  if (session) {
    if (!inviteToken) return <Navigate to="/" replace />;
    // The invite page greets a just-registered user instead of saying "already a Member".
    return <Navigate to={`/invitasjon/${inviteToken}`} replace state={{ justRegistered: true }} />;
  }

  function showErrors(next: FieldErrors) {
    flushSync(() => setErrors(next));
    focusFirstInvalid(formRef.current, next);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const input = {
      email: String(data.get('email') ?? '').trim(),
      name: String(data.get('name') ?? ''),
      password: String(data.get('password') ?? ''),
    };
    setFormError(null);
    setEmailTaken(false);
    const invalid = validateRegister(input);
    if (Object.keys(invalid).length > 0) return showErrors(invalid);
    setErrors({});
    register.mutate(inviteToken ? { ...input, invite_token: inviteToken } : input, {
      onError: (error) => {
        if (error instanceof AuthError && error.status === 409) {
          setEmailTaken(true);
          showErrors({ email: error.message });
        } else if (error instanceof AuthError && Object.keys(error.fields).length > 0) {
          showErrors(error.fields);
        } else {
          setFormError(MESSAGES.unknown);
        }
      },
    });
  }

  return (
    <div className="auth-page">
      <h1 className="auth-page__title">Opprett konto</h1>
      <form ref={formRef} className="auth-form" onSubmit={handleSubmit} noValidate>
        <TextField
          label="E-post"
          name="email"
          type="email"
          autoComplete="email"
          error={errors.email}
          errorAction={emailTaken ? <Link to={signInPath}>Logg inn i stedet</Link> : undefined}
        />
        <TextField
          label="Navn"
          name="name"
          autoComplete="name"
          hint="Slik ser de andre i hjemmet deg, for eksempel «Mari»."
          error={errors.name}
        />
        <TextField
          label="Passord"
          name="password"
          type="password"
          autoComplete="new-password"
          hint={`Minst ${PASSWORD_MIN} tegn.`}
          error={errors.password}
        />
        {formError && (
          <p className="auth-form__error" role="alert">
            {formError}
          </p>
        )}
        <PrimaryButton type="submit" pending={register.isPending}>
          Opprett konto
        </PrimaryButton>
      </form>
      <p className="auth-page__switch">
        Har du allerede en konto? <Link to={signInPath}>Logg inn</Link>
      </p>
    </div>
  );
}

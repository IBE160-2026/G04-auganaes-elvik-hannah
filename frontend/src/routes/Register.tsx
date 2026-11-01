// Story 1.2 (FR-1): create an account with email, display name and password.
import { useRef, useState, type FormEvent } from 'react';
import { flushSync } from 'react-dom';
import { Link, Navigate } from 'react-router';
import { AuthError, MESSAGES, PASSWORD_MIN, validateRegister, type FieldErrors } from '../api/auth';
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

  if (session) return <Navigate to="/" replace />;

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
    register.mutate(input, {
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
          errorAction={emailTaken ? <Link to="/logg-inn">Logg inn i stedet</Link> : undefined}
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
        Har du allerede en konto? <Link to="/logg-inn">Logg inn</Link>
      </p>
    </div>
  );
}

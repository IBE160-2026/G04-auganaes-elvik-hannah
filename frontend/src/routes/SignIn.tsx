// Story 1.2 (FR-1): sign in. A wrong email or password shows one inline error, no reload.
import { useRef, useState, type FormEvent } from 'react';
import { flushSync } from 'react-dom';
import { Link, Navigate } from 'react-router';
import { AuthError, MESSAGES, validateSignIn, type FieldErrors } from '../api/auth';
import { useSignIn } from '../api/queries';
import { useSession } from '../api/session';
import { PrimaryButton } from '../components/PrimaryButton';
import { TextField } from '../components/TextField';
import { focusFirstInvalid } from './formFocus';
import './AuthForm.css';

export function SignIn() {
  const session = useSession();
  const signIn = useSignIn();
  const formRef = useRef<HTMLFormElement>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);

  if (session) return <Navigate to="/" replace />;

  function showErrors(next: FieldErrors) {
    // Render aria-invalid and the message first, so screen readers announce the error on focus.
    flushSync(() => setErrors(next));
    focusFirstInvalid(formRef.current, next);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const input = { email: String(data.get('email') ?? '').trim(), password: String(data.get('password') ?? '') };
    setFormError(null);
    const invalid = validateSignIn(input);
    if (Object.keys(invalid).length > 0) return showErrors(invalid);
    setErrors({});
    signIn.mutate(input, {
      onError: (error) => {
        if (error instanceof AuthError && error.status === 401) {
          showErrors({ password: error.message });
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
      <h1 className="auth-page__title">Logg inn</h1>
      <form ref={formRef} className="auth-form" onSubmit={handleSubmit} noValidate>
        <TextField label="E-post" name="email" type="email" autoComplete="email" error={errors.email} />
        <TextField
          label="Passord"
          name="password"
          type="password"
          autoComplete="current-password"
          error={errors.password}
        />
        {formError && (
          <p className="auth-form__error" role="alert">
            {formError}
          </p>
        )}
        <PrimaryButton type="submit" pending={signIn.isPending}>
          Logg inn
        </PrimaryButton>
      </form>
      <p className="auth-page__switch">
        Ny i Husly? <Link to="/registrer">Opprett konto</Link>
      </p>
    </div>
  );
}

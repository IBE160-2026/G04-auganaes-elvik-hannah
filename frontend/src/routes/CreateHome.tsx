// Story 1.3 (FR-1, FR-3): create a Household Home or a Landlord Home. The types offered come
// from the server's allowed_types, so the creation rule lives only in the backend domain.
// Story 1.8: the no-Home state after leaving shows «Du har forlatt «X».»
import { useId, useRef, useState, type FormEvent } from 'react';
import { flushSync } from 'react-dom';
import { Navigate, useNavigate } from 'react-router';
import { ApiError, fieldsOf } from '../api/errors';
import {
  HOME_MESSAGES,
  TYPE_LABELS,
  validateCreateHome,
  type HomeFieldErrors,
  type HomeType,
} from '../api/homes';
import { useCreateHome, useHomes } from '../api/queries';
import { PendingNotice } from '../components/PendingNotice';
import { PrimaryButton } from '../components/PrimaryButton';
import { TextField } from '../components/TextField';
import { HomesLoadError } from './HomesLoadError';
import { focusFirstInvalid } from './formFocus';
import './AuthForm.css';
import './CreateHome.css';

const TYPE_DESCRIPTIONS: Record<HomeType, string> = {
  household: 'Dere bor sammen og deler på husarbeidet. Alle i hjemmet er likestilte.',
  landlord: 'Du leier ut og følger opp vedlikeholdet sammen med leietakerne.',
};

export function CreateHome() {
  const homes = useHomes();
  const createHome = useCreateHome();
  const navigate = useNavigate();
  const formRef = useRef<HTMLFormElement>(null);
  const typeErrorId = useId();
  const [errors, setErrors] = useState<HomeFieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);

  if (homes.isPending) return <p role="status">Laster …</p>;
  // A failed background refetch keeps the cached data; only a load with nothing to show is an error.
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;

  const allowed = homes.data.allowed_types;
  // Nothing to create (a Household Member or Tenant): back to their Home page. Not while a
  // create is in flight or just done, since the cache then holds a placeholder.
  if (allowed.length === 0 && !createHome.isPending && !createHome.isSuccess) {
    return <Navigate to="/" replace />;
  }
  const onlyType = allowed.length === 1 ? allowed[0] : null;
  const isFirstHome = homes.data.homes.length === 0;

  function showErrors(next: HomeFieldErrors) {
    // Render aria-invalid and the message first, so screen readers announce the error on focus.
    flushSync(() => setErrors(next));
    focusFirstInvalid(formRef.current, next);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const name = String(data.get('name') ?? '').trim();
    const chosen = onlyType ?? (data.get('type') as HomeType | null);
    setFormError(null);
    const invalid = validateCreateHome(name, chosen);
    if (Object.keys(invalid).length > 0 || !chosen) return showErrors(invalid);
    setErrors({});
    createHome.mutate(
      { name, type: chosen },
      {
        onSuccess: () => navigate('/', { replace: true }),
        onError: (error) => {
          if (error instanceof ApiError && Object.keys(error.fields).length > 0) {
            showErrors(fieldsOf<HomeFieldErrors>(error));
          } else if (error instanceof ApiError && error.status === 409) {
            setFormError(error.message);
            // The allowed types changed (e.g. a Home made in another tab): re-render from the
            // server's, which sends the user to "/" when none remain.
            void homes.refetch();
          } else {
            setFormError(HOME_MESSAGES.unknown);
          }
        },
      },
    );
  }

  return (
    <div className="auth-page">
      <PendingNotice className="create-home__notice" />
      <h1 className="auth-page__title">
        {isFirstHome ? 'Opprett hjemmet ditt' : 'Opprett ny utleiebolig'}
      </h1>
      {isFirstHome && (
        <p className="create-home__lead">Bor dere sammen, eller leier du ut? Velg det som passer.</p>
      )}
      <form ref={formRef} className="auth-form" onSubmit={handleSubmit} noValidate>
        {!onlyType && (
          <fieldset className="create-home__types">
            <legend className="create-home__legend">Hva slags hjem er dette?</legend>
            {allowed.map((type) => (
              <label key={type} className="create-home__type">
                <input
                  type="radio"
                  name="type"
                  value={type}
                  className="create-home__radio"
                  aria-invalid={errors.type ? true : undefined}
                  aria-describedby={errors.type ? typeErrorId : undefined}
                />
                <span className="create-home__type-text">
                  <span className="create-home__type-name">{TYPE_LABELS[type]}</span>
                  <span className="create-home__type-description">{TYPE_DESCRIPTIONS[type]}</span>
                </span>
              </label>
            ))}
            {errors.type && (
              <p id={typeErrorId} className="create-home__error">
                {errors.type}
              </p>
            )}
          </fieldset>
        )}
        <TextField
          label="Navn på hjemmet"
          name="name"
          autoComplete="off"
          hint="For eksempel «Kollektivet i Storgata»."
          error={errors.name}
        />
        {formError && (
          <p className="auth-form__error" role="alert">
            {formError}
          </p>
        )}
        <PrimaryButton type="submit" pending={createHome.isPending}>
          Opprett hjem
        </PrimaryButton>
      </form>
    </div>
  );
}

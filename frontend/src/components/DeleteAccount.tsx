// Story 1.10 (FR-25): «Slett konto» under Settings. An inline confirmation like the leave and remove
// confirmations (Story 1.8), but with the password, since the deletion cannot be undone and a stolen
// session must not be enough. Nothing is sent until the password is given and «Ja, slett kontoen»
// is pressed. The server's own texts for a wrong password (400) and a Landlord who still has
// Tenants (409) are shown inline; a success clears the session, and the routes send the user to
// sign-in.
import { useId, useRef, useState, type FormEvent } from 'react';
import { flushSync } from 'react-dom';
import { DELETE_ACCOUNT_MESSAGES } from '../api/auth';
import { useDeleteAccount } from '../api/queries';
import { PENDING_LABEL } from './PrimaryButton';
import './ConfirmAction.css';
import './DeleteAccount.css';

export function DeleteAccount() {
  const [open, setOpen] = useState(false);
  const [missing, setMissing] = useState(false);
  const remove = useDeleteAccount();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const passwordId = useId();
  const explanationId = useId();
  const errorId = useId();

  function reveal() {
    flushSync(() => setOpen(true));
    passwordRef.current?.focus();
  }

  function cancel() {
    remove.reset();
    setMissing(false);
    flushSync(() => setOpen(false));
    triggerRef.current?.focus();
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (remove.isPending) return;
    const password = String(new FormData(event.currentTarget).get('password') ?? '');
    setMissing(password === '');
    if (password === '') {
      passwordRef.current?.focus();
      return;
    }
    remove.mutate(password);
  }

  if (!open) {
    return (
      <button ref={triggerRef} type="button" className="confirm-action__trigger" onClick={reveal}>
        Slett konto
      </button>
    );
  }

  const message = missing ? DELETE_ACCOUNT_MESSAGES.passwordMissing : remove.error?.message;
  return (
    <form className="confirm-action delete-account" onSubmit={submit} noValidate>
      <p id={explanationId} className="confirm-action__explanation">
        {DELETE_ACCOUNT_MESSAGES.explanation}
      </p>
      <label className="delete-account__label" htmlFor={passwordId}>
        {DELETE_ACCOUNT_MESSAGES.passwordLabel}
      </label>
      <input
        ref={passwordRef}
        id={passwordId}
        name="password"
        type="password"
        autoComplete="current-password"
        className="delete-account__input"
        aria-describedby={message ? `${explanationId} ${errorId}` : explanationId}
        aria-invalid={message ? true : undefined}
      />
      {message && (
        <p id={errorId} className="confirm-action__error" role="alert">
          {message}
        </p>
      )}
      <div className="confirm-action__buttons">
        <button
          type="submit"
          className="confirm-action__confirm"
          aria-disabled={remove.isPending || undefined}
          aria-busy={remove.isPending || undefined}
        >
          {remove.isPending ? PENDING_LABEL : 'Ja, slett kontoen'}
        </button>
        <button type="button" className="confirm-action__cancel" onClick={cancel}>
          Avbryt
        </button>
      </div>
    </form>
  );
}

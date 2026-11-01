import { useId, type ReactNode } from 'react';
import './TextField.css';

type TextFieldProps = {
  label: string;
  name: string;
  type?: 'text' | 'email' | 'password';
  autoComplete: string;
  /** Shown under the field, tied to it with aria-describedby, and marks it aria-invalid. */
  error?: string;
  /** Extra content after the error, e.g. a "Logg inn i stedet" link. */
  errorAction?: ReactNode;
  hint?: string;
};

/** A labelled input with its own inline error (Story 1.2, EXPERIENCE.md accessibility floor). */
export function TextField({
  label,
  name,
  type = 'text',
  autoComplete,
  error,
  errorAction,
  hint,
}: TextFieldProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(' ') || undefined;

  return (
    <div className="text-field">
      <label className="text-field__label" htmlFor={id}>
        {label}
      </label>
      {hint && (
        <p id={hintId} className="text-field__hint">
          {hint}
        </p>
      )}
      <input
        id={id}
        className="text-field__input"
        name={name}
        type={type}
        autoComplete={autoComplete}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
      />
      {error && (
        <p id={errorId} className="text-field__error">
          {error} {errorAction}
        </p>
      )}
    </div>
  );
}

// Story 1.8 (FR-23, EXPERIENCE.md "Leave / remove confirmation"): an inline confirmation, not a
// modal. The first button turns into an explanation, a confirm button in the danger colour with
// its text label, and «Avbryt». Nothing is sent until the confirm button is pressed.
import { useId, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { PENDING_LABEL } from './PrimaryButton';
import './ConfirmAction.css';

type ConfirmActionProps = {
  /** The first button's text, e.g. «Forlat hjemmet» or «Fjern». */
  label: string;
  /** The first button's accessible name when the text alone is not enough («Fjern Anders»). */
  ariaLabel?: string;
  /** What happens, shown once the first button is pressed. */
  explanation: string;
  /** The confirm button's text, e.g. «Ja, forlat hjemmet». */
  confirmLabel: string;
  /** The confirm button's accessible name when the text alone is not enough (Story 2.6). */
  confirmAriaLabel?: string;
  /** `close` folds the confirmation back to the first button and focuses it (e.g. after a 403). */
  onConfirm: (close: () => void) => void;
  /** Called on «Avbryt», e.g. to clear a failed attempt. */
  onCancel?: () => void;
  pending?: boolean;
  /** A failed attempt, shown inline; the confirm button then retries («Prøv igjen»). */
  error?: string | null;
};

export function ConfirmAction({
  label,
  ariaLabel,
  explanation,
  confirmLabel,
  confirmAriaLabel,
  onConfirm,
  onCancel,
  pending = false,
  error = null,
}: ConfirmActionProps) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);
  const explanationId = useId();

  function reveal() {
    flushSync(() => setOpen(true));
    confirmRef.current?.focus();
  }

  function close() {
    flushSync(() => setOpen(false));
    triggerRef.current?.focus();
  }

  function cancel() {
    onCancel?.();
    close();
  }

  function confirm() {
    // aria-disabled rather than disabled while sending, so focus stays on the button.
    if (!pending) onConfirm(close);
  }

  if (!open) {
    return (
      <button
        ref={triggerRef}
        type="button"
        className="confirm-action__trigger"
        aria-label={ariaLabel}
        onClick={reveal}
      >
        {label}
      </button>
    );
  }

  return (
    <div className="confirm-action">
      <p id={explanationId} className="confirm-action__explanation">
        {explanation}
      </p>
      {error && (
        <p className="confirm-action__error" role="alert">
          {error}
        </p>
      )}
      <div className="confirm-action__buttons">
        <button
          ref={confirmRef}
          type="button"
          className="confirm-action__confirm"
          aria-label={pending || error ? undefined : confirmAriaLabel}
          aria-describedby={explanationId}
          aria-disabled={pending || undefined}
          aria-busy={pending || undefined}
          onClick={confirm}
        >
          {pending ? PENDING_LABEL : error ? 'Prøv igjen' : confirmLabel}
        </button>
        <button type="button" className="confirm-action__cancel" onClick={cancel}>
          Avbryt
        </button>
      </div>
    </div>
  );
}

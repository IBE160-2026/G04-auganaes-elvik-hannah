import { useId, type MouseEvent, type ReactNode } from 'react';
import './PrimaryButton.css';

export const PENDING_LABEL = 'Sender…';

type PrimaryButtonProps = {
  children: ReactNode;
  onClick?: (event: MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit';
  /** In-flight: label swaps to "Sender…" and clicks are ignored (DESIGN.md Components). */
  pending?: boolean;
  disabled?: boolean;
  /** Shown under the button and linked with aria-describedby when it is disabled. */
  disabledReason?: string;
};

/**
 * The one dominant action on a screen (Story 1.1, FR-21).
 * Uses aria-disabled instead of the native disabled attribute so the button stays
 * focusable and screen readers can reach the reason it is unavailable.
 */
export function PrimaryButton({
  children,
  onClick,
  type = 'button',
  pending = false,
  disabled = false,
  disabledReason,
}: PrimaryButtonProps) {
  const reasonId = useId();
  const inactive = pending || disabled;
  const showReason = disabled && !pending && Boolean(disabledReason);

  function handleClick(event: MouseEvent<HTMLButtonElement>) {
    if (inactive) {
      event.preventDefault();
      return;
    }
    onClick?.(event);
  }

  return (
    <div className="primary-button-group">
      <button
        type={type}
        className="primary-button"
        aria-disabled={inactive || undefined}
        aria-busy={pending || undefined}
        aria-describedby={showReason ? reasonId : undefined}
        onClick={handleClick}
      >
        {pending ? PENDING_LABEL : children}
      </button>
      {showReason && (
        <p id={reasonId} className="primary-button__reason">
          {disabledReason}
        </p>
      )}
    </div>
  );
}

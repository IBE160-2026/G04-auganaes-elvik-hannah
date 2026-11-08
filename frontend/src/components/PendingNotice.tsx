// Story 1.8: shows a one-time notice left by the previous page («Du har forlatt «X».»). Render
// it only where the page is actually shown, never next to a redirect, which would consume it.
import { useNotice } from '../api/queries';

export function PendingNotice({ className }: { className: string }) {
  const notice = useNotice();
  // Always in the DOM, so the text is announced when it arrives. No role="status": the pages'
  // loading text («Laster …») already uses it.
  return (
    <p className={className} aria-live="polite">
      {notice}
    </p>
  );
}

import { HOME_MESSAGES } from '../api/homes';
import { PrimaryButton } from '../components/PrimaryButton';
import './AuthForm.css';

/** Story 1.3: GET /api/homes failed. Inline, with a retry; never a redirect. */
export function HomesLoadError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="auth-page">
      <p className="auth-form__error" role="alert">
        {HOME_MESSAGES.loadFailed}
      </p>
      <PrimaryButton onClick={onRetry}>Prøv igjen</PrimaryButton>
    </div>
  );
}

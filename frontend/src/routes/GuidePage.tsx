// Story 5.3 (FR-16): Settings → Velkomstguide, at /hjem/<id>/velkommen. The same guide as the
// card, as a page that can always be read again, by a Tenant or the Landlord (to see what the
// Tenants are told). Guards: an unknown Home goes to "/", a Home that may not show the guide or
// has none goes back to its overview.
import { Link, Navigate, useParams } from 'react-router';
import { ApiError } from '../api/errors';
import { GUIDE_MESSAGES } from '../api/onboarding';
import { useHomes, useOnboardingGuide } from '../api/queries';
import { OnboardingGuide } from '../components/OnboardingGuide';
import { HomesLoadError } from './HomesLoadError';
import { useFocusOnMount } from './useFocusOnMount';
import './AuthForm.css';

export function GuidePage() {
  const { homeId } = useParams();
  const homes = useHomes();
  if (homes.isPending) return <p role="status">Laster …</p>;
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  const home = homes.data.homes.find((h) => h.id === homeId);
  if (!home) return <Navigate to="/" replace />;
  if (!home.can_view_guide) return <Navigate to={`/hjem/${home.id}`} replace />;
  return <Guide key={home.id} homeId={home.id} />;
}

function Guide({ homeId }: { homeId: string }) {
  const guide = useOnboardingGuide(homeId, true);
  const titleRef = useFocusOnMount<HTMLHeadingElement>();
  if (guide.error instanceof ApiError && guide.error.status === 403) return null;
  if (guide.error instanceof ApiError && guide.error.status === 404) {
    return <Navigate to={`/hjem/${homeId}`} replace />;
  }
  return (
    <div className="guide-page">
      {guide.data ? (
        <OnboardingGuide guide={guide.data} headingLevel={1} titleRef={titleRef} />
      ) : guide.isError ? (
        <>
          <p className="auth-form__error" role="alert">
            {GUIDE_MESSAGES.loadFailed}
          </p>
          <button type="button" onClick={() => void guide.refetch()}>
            Prøv igjen
          </button>
        </>
      ) : (
        <p role="status">Laster …</p>
      )}
      <Link to={`/hjem/${homeId}`}>{GUIDE_MESSAGES.backToHome}</Link>
    </div>
  );
}

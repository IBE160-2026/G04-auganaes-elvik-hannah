// Story 1.3: the post-creation landing page. Shows the newest Home, the user's Role in it and
// "Logg ut"; Landlords also see their Homes and "Opprett nytt hjem". Task Overview replaces this
// page in Stories 2.1–2.2, and the tab bar comes with Story 2.2. Story 1.4: links to
// "Medlemmer og invitasjon" for the shown Home, and for each of a Landlord's Homes.
import { Link, Navigate } from 'react-router';
import { ROLE_LABELS, TYPE_LABELS } from '../api/homes';
import { useHomes, useMe, useSignOut } from '../api/queries';
import { PrimaryButton } from '../components/PrimaryButton';
import { HomesLoadError } from './HomesLoadError';
import './HomePage.css';

export function HomePage() {
  const me = useMe();
  const homes = useHomes();
  const signOut = useSignOut();

  if (homes.isPending) return <p role="status">Laster …</p>;
  // A failed background refetch keeps the cached data; only a load with nothing to show is an error.
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  // Only a loaded, empty list sends the user to Create Home.
  if (homes.data.homes.length === 0) return <Navigate to="/nytt-hjem" replace />;

  const [home] = homes.data.homes;
  const isLandlord = homes.data.homes.some((h) => h.role === 'landlord');
  const canCreate = homes.data.allowed_types.length > 0;
  const firstName = me.data?.name.split(' ')[0];

  return (
    <div className="home-page">
      <h1 className="home-page__title">{home.name}</h1>
      {home.type === 'household' ? (
        <p className="home-page__lead">Velkommen hjem{firstName ? `, ${firstName}` : ''}! Her deler dere på husarbeidet.</p>
      ) : (
        <p className="home-page__lead">Du er logget inn som {me.data?.name}.</p>
      )}
      <dl className="home-page__facts">
        <div>
          <dt>Type</dt>
          <dd>{TYPE_LABELS[home.type]}</dd>
        </div>
        <div>
          <dt>Din rolle</dt>
          <dd>{ROLE_LABELS[home.role]}</dd>
        </div>
      </dl>
      <Link to={`/hjem/${home.id}/medlemmer`} className="home-page__link">
        Medlemmer og invitasjon
      </Link>
      {isLandlord && (
        <section className="home-page__section" aria-labelledby="home-page-homes">
          <h2 id="home-page-homes" className="home-page__subtitle">
            Dine hjem
          </h2>
          <ul className="home-page__list">
            {homes.data.homes.map((h) => (
              <li key={h.id}>
                {h.name} <span className="home-page__meta">({ROLE_LABELS[h.role]})</span>{' '}
                <Link
                  to={`/hjem/${h.id}/medlemmer`}
                  className="home-page__list-link"
                  aria-label={`Medlemmer og invitasjon for ${h.name}`}
                >
                  Medlemmer
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
      {canCreate && (
        <Link to="/nytt-hjem" className="home-page__link">
          Opprett nytt hjem
        </Link>
      )}
      <PrimaryButton onClick={() => signOut.mutate()} pending={signOut.isPending}>
        Logg ut
      </PrimaryButton>
    </div>
  );
}

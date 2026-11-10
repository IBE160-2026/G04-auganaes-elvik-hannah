// Story 1.3: "/" sends a user without a Home to Create Home.
// Story 2.2 (decision 3): "/" only redirects. It opens the most recently used Home on this
// device if it is still in the server's list, else the Home the user lives in, else the first.
// The Task Overview at /hjem/<id> has the guards, the tasks and the Story 1.8 leave notice.
import { Navigate } from 'react-router';
import { pickHome, readLastHome } from '../api/lastHome';
import { useHomes } from '../api/queries';
import { useSession } from '../api/session';
import { HomesLoadError } from './HomesLoadError';

export function HomePage() {
  const userId = useSession()?.user.id;
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  // A failed background refetch keeps the cached data; only a load with nothing to show is an error.
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  const home = pickHome(homes.data, readLastHome(userId));
  // Only a loaded, empty list sends the user to Create Home.
  if (!home) return <Navigate to="/nytt-hjem" replace />;
  return <Navigate to={`/hjem/${home.id}`} replace />;
}

// Story 2.2 (decision 13, UX-DR36): the tab bar, «Oppgaver» and «Innstillinger». Rendered only
// with a session and a loaded Homes list with at least one Home, so it is absent when signed
// out, on sign-in/register, while the Homes load or fail, and for a user without a Home.
// AppShell wraps SessionGate, so this reads the session and Homes itself and never assumes them.
// It only reads the Homes the page loaded (useLoadedHomes), so the list is never fetched twice.
// «Oppgaver» opens the Home in the URL (/hjem/<id>/…), else the Home "/" would open. The
// Portfolio tab comes with Story 6.1 (decision 5).
import { Link, useLocation, useMatch } from 'react-router';
import { pickHome, readLastHome } from '../api/lastHome';
import { useLoadedHomes } from '../api/queries';
import { useSession } from '../api/session';
import './TabBar.css';

export function TabBar() {
  const session = useSession();
  const homes = useLoadedHomes();
  const inHome = useMatch('/hjem/:homeId/*');
  const { pathname } = useLocation();

  if (!session || !homes.data || homes.data.homes.length === 0) return null;
  const urlHomeId = inHome?.params.homeId;
  const home =
    homes.data.homes.find((h) => h.id === urlHomeId) ?? pickHome(homes.data, readLastHome(session.user.id));
  if (!home) return null;
  const onSettings = pathname === '/innstillinger';

  return (
    <nav className="tab-bar" aria-label="Hovedmeny">
      <ul className="tab-bar__list">
        <li className="tab-bar__item">
          <Link to={`/hjem/${home.id}`} className="tab-bar__tab" aria-current={inHome ? 'page' : undefined}>
            Oppgaver
          </Link>
        </li>
        <li className="tab-bar__item">
          <Link to="/innstillinger" className="tab-bar__tab" aria-current={onSettings ? 'page' : undefined}>
            Innstillinger
          </Link>
        </li>
      </ul>
    </nav>
  );
}

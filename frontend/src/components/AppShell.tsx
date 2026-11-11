import type { ReactNode } from 'react';
import { Link } from 'react-router';
import { TabBar } from './TabBar';
import './AppShell.css';

type AppShellProps = {
  children: ReactNode;
};

/**
 * Responsive shell shared by every screen (Story 1.1, FR-21). Story 2.2: the «Husly» wordmark is
 * a real link to "/", and the tab bar follows main (it decides itself whether to show).
 */
export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <a className="app-shell__skip-link" href="#hovedinnhold">
        Hopp til hovedinnhold
      </a>
      <header className="app-shell__header">
        <div className="app-shell__header-inner">
          <Link to="/" className="app-shell__brand">
            Husly
          </Link>
        </div>
      </header>
      <main id="hovedinnhold" className="app-shell__main" tabIndex={-1}>
        {children}
      </main>
      <TabBar />
    </div>
  );
}

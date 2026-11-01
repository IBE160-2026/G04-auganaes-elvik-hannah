import type { ReactNode } from 'react';
import './AppShell.css';

type AppShellProps = {
  children: ReactNode;
};

/** Responsive shell shared by every screen (Story 1.1, FR-21). */
export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <a className="app-shell__skip-link" href="#hovedinnhold">
        Hopp til hovedinnhold
      </a>
      <header className="app-shell__header">
        <div className="app-shell__header-inner">
          <span className="app-shell__brand">Husly</span>
        </div>
      </header>
      <main id="hovedinnhold" className="app-shell__main" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}

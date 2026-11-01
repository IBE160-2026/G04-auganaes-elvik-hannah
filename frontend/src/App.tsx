import { AppShell } from './components/AppShell';
import { InstallPrompt } from './components/InstallPrompt';
import { PrimaryButton } from './components/PrimaryButton';
import './App.css';

/** Placeholder start page until routes arrive with Story 1.2. */
export function App() {
  return (
    <AppShell>
      <div className="start-page">
        <h1 className="start-page__title">Velkommen til Husly</h1>
        <p className="start-page__lead">
          Her skal dere snart kunne fordele og huske oppgavene i hjemmet, enten dere bor sammen
          eller leier ut.
        </p>
        <PrimaryButton disabled disabledReason="Innlogging kommer i neste versjon av appen.">
          Kom i gang
        </PrimaryButton>
      </div>
      <InstallPrompt />
    </AppShell>
  );
}

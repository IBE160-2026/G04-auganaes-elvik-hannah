// Story 1.2: the protected start page. No tab bar yet; it arrives with Story 1.3.
import { useMe, useSignOut } from '../api/queries';
import { PrimaryButton } from '../components/PrimaryButton';
import './Start.css';

export function Start() {
  const me = useMe();
  const signOut = useSignOut();

  return (
    <div className="start-page">
      <h1 className="start-page__title">Velkommen til Husly</h1>
      {me.data && <p className="start-page__lead">Du er logget inn som {me.data.name}</p>}
      <PrimaryButton onClick={() => signOut.mutate()} pending={signOut.isPending}>
        Logg ut
      </PrimaryButton>
    </div>
  );
}

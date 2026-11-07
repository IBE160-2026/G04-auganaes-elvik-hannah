import { QueryClientProvider, type QueryClient } from '@tanstack/react-query';
import { useEffect, useState, type ReactNode } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router';
import { refreshSession } from './api/client';
import { createQueryClient } from './api/queries';
import { AppShell } from './components/AppShell';
import { InstallPrompt } from './components/InstallPrompt';
import { CreateHome } from './routes/CreateHome';
import { HomePage } from './routes/HomePage';
import { Register } from './routes/Register';
import { RequireAuth } from './routes/RequireAuth';
import { SignIn } from './routes/SignIn';

/**
 * Restores the session from the refresh cookie once, before any route renders, so a reload
 * keeps the user signed in (Story 1.2). StrictMode's second effect shares the same refresh.
 */
function SessionGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let active = true;
    void refreshSession().then(() => {
      if (active) setReady(true);
    });
    return () => {
      active = false;
    };
  }, []);
  if (!ready) return <p role="status">Laster …</p>;
  return children;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/logg-inn" element={<SignIn />} />
      <Route path="/registrer" element={<Register />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        }
      />
      <Route
        path="/nytt-hjem"
        element={
          <RequireAuth>
            <CreateHome />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export function App({ queryClient }: { queryClient?: QueryClient }) {
  const [client] = useState(() => queryClient ?? createQueryClient());
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <AppShell>
          <SessionGate>
            <AppRoutes />
          </SessionGate>
          <InstallPrompt />
        </AppShell>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

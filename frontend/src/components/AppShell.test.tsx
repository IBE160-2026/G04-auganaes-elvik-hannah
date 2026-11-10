// Story 1.1 (FR-21): the shell's landmarks and skip link.
// Story 2.2 (decision 13): the «Husly» wordmark links to "/", and the tab bar shows only with a
// session and a loaded Homes list with at least one Home.
import { QueryClientProvider } from '@tanstack/react-query';
import { render, screen, within } from '@testing-library/react';
import type { ReactNode } from 'react';
import { MemoryRouter } from 'react-router';
import { createQueryClient, useHomes } from '../api/queries';
import { setSession } from '../api/session';
import { OLA, OLAS_HOME, fakeApi, homesResponse, json, resetApi } from '../test-utils/fakeApi';
import { AppShell } from './AppShell';

function renderShell(children: ReactNode, path = '/') {
  return render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <AppShell>{children}</AppShell>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

// Like every signed-in page: loads the Homes list, which the tab bar only reads.
function Page() {
  useHomes();
  return <p>Innhold</p>;
}

function signIn() {
  setSession({ accessToken: 'a1', user: OLA });
}

afterEach(resetApi);

describe('AppShell', () => {
  it('has one banner and one main landmark, with children inside main', () => {
    renderShell(<p>Innhold</p>);

    expect(screen.getAllByRole('banner')).toHaveLength(1);
    const main = screen.getByRole('main');
    expect(screen.getAllByRole('main')).toHaveLength(1);
    expect(main).toContainElement(screen.getByText('Innhold'));
  });

  it('skip link points at main, which can take focus', () => {
    renderShell('Innhold');

    const link = screen.getByRole('link', { name: 'Hopp til hovedinnhold' });
    const main = screen.getByRole('main');
    expect(link).toHaveAttribute('href', `#${main.id}`);
    expect(main.id).not.toBe('');
    expect(main).toHaveAttribute('tabindex', '-1');
  });

  it('makes the «Husly» wordmark a real link to "/", also signed out', () => {
    renderShell('Innhold', '/logg-inn');

    const brand = within(screen.getByRole('banner')).getByRole('link', { name: 'Husly' });
    expect(brand.tagName).toBe('A');
    expect(brand).toHaveAttribute('href', '/');
  });
});

describe('Tab bar', () => {
  it('is absent when signed out', () => {
    fakeApi({});
    renderShell(<Page />, '/logg-inn');
    expect(screen.queryByRole('navigation', { name: 'Hovedmeny' })).not.toBeInTheDocument();
  });

  it('is absent while the Homes load', async () => {
    const server = fakeApi({ 'GET /api/homes': () => new Promise<Response>(() => {}) });
    signIn();
    renderShell(<Page />);
    await vi.waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(1));
    expect(screen.queryByRole('navigation', { name: 'Hovedmeny' })).not.toBeInTheDocument();
  });

  it('is absent when the Homes fail to load', async () => {
    const server = fakeApi({ 'GET /api/homes': () => json(500, { detail: 'x' }) });
    signIn();
    renderShell(<Page />);
    await vi.waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(1));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.queryByRole('navigation', { name: 'Hovedmeny' })).not.toBeInTheDocument();
  });

  it('is absent for a user without a Home', async () => {
    const server = fakeApi({ 'GET /api/homes': () => json(200, homesResponse([], ['household'])) });
    signIn();
    renderShell(<Page />, '/nytt-hjem');
    await vi.waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(1));
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.queryByRole('navigation', { name: 'Hovedmeny' })).not.toBeInTheDocument();
  });

  it.each([
    [`/hjem/${OLAS_HOME.id}`, 'Oppgaver'],
    [`/hjem/${OLAS_HOME.id}/medlemmer`, 'Oppgaver'],
    [`/hjem/${OLAS_HOME.id}/oppgaver/x`, 'Oppgaver'],
    [`/hjem/${OLAS_HOME.id}/oppgaveoppsett`, 'Oppgaver'],
    ['/innstillinger', 'Innstillinger'],
    ['/nytt-hjem', null],
  ])('on %s marks %s as the current page, after main', async (path, current) => {
    fakeApi({ 'GET /api/homes': () => json(200, homesResponse()) });
    signIn();
    renderShell(<Page />, path);

    const nav = await screen.findByRole('navigation', { name: 'Hovedmeny' });
    const tasks = within(nav).getByRole('link', { name: 'Oppgaver' });
    const settings = within(nav).getByRole('link', { name: 'Innstillinger' });
    expect(tasks).toHaveAttribute('href', `/hjem/${OLAS_HOME.id}`);
    expect(settings).toHaveAttribute('href', '/innstillinger');
    const marked = [tasks, settings].filter((link) => link.getAttribute('aria-current') === 'page');
    expect(marked.map((link) => link.textContent)).toEqual(current ? [current] : []);
    // Keyboard order: the tab bar comes after the page content.
    expect(screen.getByRole('main').compareDocumentPosition(nav) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

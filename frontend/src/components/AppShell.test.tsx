// Story 1.1 (FR-21): the shell's landmarks and skip link.
import { render, screen } from '@testing-library/react';
import { AppShell } from './AppShell';

describe('AppShell', () => {
  it('has one banner and one main landmark, with children inside main', () => {
    render(
      <AppShell>
        <p>Innhold</p>
      </AppShell>,
    );

    expect(screen.getAllByRole('banner')).toHaveLength(1);
    const main = screen.getByRole('main');
    expect(screen.getAllByRole('main')).toHaveLength(1);
    expect(main).toContainElement(screen.getByText('Innhold'));
  });

  it('skip link points at main, which can take focus', () => {
    render(<AppShell>Innhold</AppShell>);

    const link = screen.getByRole('link', { name: 'Hopp til hovedinnhold' });
    const main = screen.getByRole('main');
    expect(link).toHaveAttribute('href', `#${main.id}`);
    expect(main.id).not.toBe('');
    expect(main).toHaveAttribute('tabindex', '-1');
  });
});

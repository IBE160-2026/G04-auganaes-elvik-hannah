// Story 1.1 (FR-21): primary button states from the I/O matrix in the spec.
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PrimaryButton } from './PrimaryButton';

describe('PrimaryButton', () => {
  it('calls onClick in the default state', async () => {
    const onClick = vi.fn();
    render(<PrimaryButton onClick={onClick}>Fullfør oppgave</PrimaryButton>);

    const button = screen.getByRole('button', { name: 'Fullfør oppgave' });
    expect(button).not.toHaveAttribute('aria-disabled');
    await userEvent.click(button);

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('shows "Sender…", is busy and ignores clicks while pending, but stays focusable', async () => {
    const onClick = vi.fn();
    render(
      <PrimaryButton onClick={onClick} pending>
        Send invitasjon
      </PrimaryButton>,
    );

    const button = screen.getByRole('button', { name: 'Sender…' });
    expect(button).toHaveAttribute('aria-busy', 'true');
    expect(button).toHaveAttribute('aria-disabled', 'true');
    expect(button).not.toBeDisabled();

    await userEvent.tab();
    expect(button).toHaveFocus();

    await userEvent.click(button);
    await userEvent.keyboard('{Enter}');
    expect(onClick).not.toHaveBeenCalled();
  });

  it('is aria-disabled with a described, visible reason and ignores clicks', async () => {
    const onClick = vi.fn();
    render(
      <PrimaryButton onClick={onClick} disabled disabledReason="Velg en oppgave først.">
        Fullfør oppgave
      </PrimaryButton>,
    );

    const button = screen.getByRole('button', { name: 'Fullfør oppgave' });
    expect(button).toHaveAttribute('aria-disabled', 'true');
    expect(button).not.toBeDisabled();
    expect(button).toHaveAccessibleDescription('Velg en oppgave først.');
    expect(screen.getByText('Velg en oppgave først.')).toBeVisible();

    await userEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('does not submit its form while disabled', async () => {
    const onSubmit = vi.fn((event: SubmitEvent) => event.preventDefault());
    render(
      <form onSubmit={(event) => onSubmit(event.nativeEvent as SubmitEvent)}>
        <PrimaryButton type="submit" disabled>
          Lagre
        </PrimaryButton>
      </form>,
    );

    await userEvent.click(screen.getByRole('button', { name: 'Lagre' }));
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('has no description when disabled without a reason', () => {
    render(<PrimaryButton disabled>Lagre</PrimaryButton>);
    expect(screen.getByRole('button', { name: 'Lagre' })).not.toHaveAttribute('aria-describedby');
  });
});

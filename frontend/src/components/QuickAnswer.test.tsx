// Story 5.1 (FR-14, UX-DR48, SM-7): the «?» popover on Task Detail, one test per matrix row.
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { AI_MESSAGES, formatReset } from '../api/ai';
import {
  DISCLAIMER,
  OLAS_HOME,
  OLAS_TASKS,
  OLAS_TENANCY,
  answerHandler,
  answerPath,
  completionPath,
  fakeApi,
  resetApi,
  signedInWith,
  taskServer,
} from '../test-utils/fakeApi';

const [MUST] = OLAS_TASKS;
const detailPath = (home: { id: string }) => `/hjem/${home.id}/oppgaver/${MUST.id}`;
const toggleName = `Spør KI om «${MUST.name}»`;

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

function setUp(outcomes?: Parameters<typeof answerHandler>[0], home = OLAS_HOME) {
  const bodies: unknown[] = [];
  const server = fakeApi({
    ...signedInWith([home]),
    [`POST ${answerPath(home, MUST)}`]: answerHandler(outcomes, bodies),
  });
  return { server, bodies };
}

async function open(home = OLAS_HOME) {
  renderAt(detailPath(home));
  const toggle = await screen.findByRole('button', { name: toggleName });
  await userEvent.click(toggle);
  return toggle;
}

afterEach(resetApi);

describe('Quick answer («?»)', () => {
  it('opens inline with a skeleton line announced politely, then shows the answer with the disclaimer', async () => {
    const { server } = setUp(['demo']);
    const toggle = await open();

    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(window.location.pathname).toBe(detailPath(OLAS_HOME));
    expect(await screen.findByText('Rens rista med hansker.')).toBeInTheDocument();
    expect(screen.getByText(DISCLAIMER)).toBeInTheDocument();
    expect(screen.getByText(AI_MESSAGES.demo)).toBeInTheDocument();
    expect(screen.getByText(AI_MESSAGES.demo).closest('[aria-live="polite"]')).not.toBeNull();
    expect(screen.queryByTestId('answer-skeleton')).not.toBeInTheDocument();
    expect(server.calls('POST', answerPath(OLAS_HOME, MUST))).toHaveLength(1);
  });

  it('shows the skeleton, not a spinner, while the call is in flight', async () => {
    setUp(['slow']);
    await open();
    const skeleton = await screen.findByTestId('answer-skeleton');
    expect(skeleton.closest('[aria-live="polite"]')).not.toBeNull();
    expect(screen.getByText(AI_MESSAGES.loading)).toBeInTheDocument();
    expect(screen.queryByText(DISCLAIMER)).not.toBeInTheDocument();
  });

  it('says the question goes to an external AI service when a real provider answered', async () => {
    setUp(['ok']);
    await open();
    expect(await screen.findByText(AI_MESSAGES.external)).toBeInTheDocument();
    expect(screen.queryByText(AI_MESSAGES.demo)).not.toBeInTheDocument();
  });

  it('sends no question on the first tap and the user’s own question from the field', async () => {
    const { bodies } = setUp(['ok']);
    await open();
    await screen.findByText('Rens rista med hansker.');
    await userEvent.type(screen.getByRole('textbox', { name: AI_MESSAGES.questionLabel }), '  Hva med kalk?  ');
    await userEvent.click(screen.getByRole('button', { name: AI_MESSAGES.ask }));
    await waitFor(() => expect(bodies).toHaveLength(2));
    expect(bodies).toEqual([{}, { question: 'Hva med kalk?' }]);
  });

  it('does not ask with a blank question', async () => {
    const { bodies } = setUp(['ok']);
    await open();
    await screen.findByText('Rens rista med hansker.');
    await userEvent.type(screen.getByRole('textbox', { name: AI_MESSAGES.questionLabel }), '   ');
    await userEvent.click(screen.getByRole('button', { name: AI_MESSAGES.ask }));
    expect(bodies).toHaveLength(1);
  });

  it('keeps the answer when the popover is closed and reopened, without a new call', async () => {
    const { server } = setUp(['ok']);
    const toggle = await open();
    await screen.findByText('Rens rista med hansker.');
    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(toggle);
    expect(screen.getByText('Rens rista med hansker.')).toBeVisible();
    expect(server.calls('POST', answerPath(OLAS_HOME, MUST))).toHaveLength(1);
  });

  it('says plainly when the AI is unsure, and still shows the disclaimer', async () => {
    setUp(['low_confidence']);
    await open();
    expect(await screen.findByText(AI_MESSAGES.unsure)).toBeInTheDocument();
    expect(screen.getByText(DISCLAIMER)).toBeInTheDocument();
  });

  it.each([['error' as const], ['network' as const], [500 as const]])(
    'shows the failure with a retry for %s, and the retry asks again',
    async (outcome) => {
      const { bodies } = setUp([outcome, 'ok']);
      await open();
      expect(await screen.findByRole('alert')).toHaveTextContent(AI_MESSAGES.failed);

      await userEvent.click(screen.getByRole('button', { name: AI_MESSAGES.retry }));
      expect(await screen.findByText('Rens rista med hansker.')).toBeInTheDocument();
      expect(bodies).toEqual([{}, {}]);
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    },
  );

  it('retries the same question it asked last', async () => {
    const { bodies } = setUp(['ok', 'error', 'ok']);
    await open();
    await screen.findByText('Rens rista med hansker.');
    await userEvent.type(screen.getByRole('textbox', { name: AI_MESSAGES.questionLabel }), 'Hva med kalk?');
    await userEvent.click(screen.getByRole('button', { name: AI_MESSAGES.ask }));
    await userEvent.click(await screen.findByRole('button', { name: AI_MESSAGES.retry }));
    await waitFor(() => expect(bodies).toHaveLength(3));
    expect(bodies[2]).toEqual({ question: 'Hva med kalk?' });
  });

  it('says the daily limit is reached and when it resets, without a retry', async () => {
    setUp(['limit']);
    await open();
    const text = await screen.findByText(/Du har brukt de 20 KI-spørsmålene dine i dag\./);
    expect(text).toHaveTextContent(`Du kan spørre igjen ${formatReset('2026-11-11T00:00:00Z')}.`);
    expect(text).toHaveTextContent(/Du kan spørre igjen \d\d\.\d\d\.2026 kl\. \d\d:\d\d\./);
    expect(screen.queryByRole('button', { name: AI_MESSAGES.retry })).not.toBeInTheDocument();
  });

  it('lets the Task be completed from the overview when no answer came (UJ-1)', async () => {
    const tasks = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET /api/homes/${OLAS_HOME.id}/tasks`]: tasks.list,
      [`POST ${answerPath(OLAS_HOME, MUST)}`]: answerHandler(['network']),
      [`POST ${completionPath(OLAS_HOME, MUST)}`]: tasks.complete(MUST),
    });
    await open();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('link', { name: 'Tilbake til oppgavene' }));
    await userEvent.click(await screen.findByRole('checkbox', { name: new RegExp(MUST.name) }));
    await waitFor(() => expect(server.calls('POST', completionPath(OLAS_HOME, MUST))).toHaveLength(1));
  });

  it('is there for a Tenant too', async () => {
    setUp(['ok'], OLAS_TENANCY);
    await open(OLAS_TENANCY);
    expect(await screen.findByText(DISCLAIMER)).toBeInTheDocument();
  });

  it('refetches the tasks on a 404 and shows nothing inline', async () => {
    const tasks = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET /api/homes/${OLAS_HOME.id}/tasks`]: tasks.list,
      [`POST ${answerPath(OLAS_HOME, MUST)}`]: answerHandler([404]),
    });
    await open();
    await waitFor(() => expect(server.calls('GET', `/api/homes/${OLAS_HOME.id}/tasks`).length).toBeGreaterThan(1));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows nothing inline on a 403 (the global handler routes), no alert and no retry', async () => {
    setUp([403]);
    await open();
    await waitFor(() => expect(screen.queryByTestId('answer-skeleton')).not.toBeInTheDocument());
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: AI_MESSAGES.retry })).not.toBeInTheDocument();
  });

  it('names the Task on the button and uses the button, not hover (a11y)', async () => {
    setUp(['ok']);
    renderAt(detailPath(OLAS_HOME));
    const toggle = await screen.findByRole('button', { name: toggleName });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(toggle).toHaveAttribute('aria-controls');
    const panel = document.getElementById(toggle.getAttribute('aria-controls') ?? '');
    expect(panel).toHaveAttribute('hidden');
    await userEvent.click(toggle);
    expect(within(panel as HTMLElement).getByRole('textbox', { name: AI_MESSAGES.questionLabel })).toBeVisible();
  });
});

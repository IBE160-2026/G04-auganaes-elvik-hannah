// Story 5.2 (FR-15, UX-DR9, NFR4): the AI chat, one test per matrix row. Opened with «Spør mer»
// from the «?» popover, or directly by its link.
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import {
  AI_MESSAGES,
  FALLBACK_DISCLAIMER,
  HISTORY_ANSWER_MAX_LENGTH,
  HISTORY_MAX_ENTRIES,
  defaultQuestion,
  formatReset,
  historyOf,
} from '../api/ai';
import {
  DISCLAIMER,
  OLAS_HOME,
  OLAS_TASKS,
  OLAS_TENANCY,
  answerHandler,
  answerPath,
  fakeApi,
  resetApi,
  signedInWith,
  taskServer,
} from '../test-utils/fakeApi';

const [MUST] = OLAS_TASKS;
const ANSWER = 'Rens rista med hansker.';
const detailPath = (home: { id: string }) => `/hjem/${home.id}/oppgaver/${MUST.id}`;
const chatPath = (home: { id: string }) => `${detailPath(home)}/chat`;
const DEFAULT_Q = defaultQuestion(MUST.name);

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

/** Opens the popover, waits for its answer and taps «Spør mer»; lands in the chat. */
async function escalate(home = OLAS_HOME) {
  renderAt(detailPath(home));
  await userEvent.click(await screen.findByRole('button', { name: `Spør KI om «${MUST.name}»` }));
  await screen.findByText(ANSWER);
  await userEvent.click(screen.getByRole('button', { name: AI_MESSAGES.askMore }));
  return screen.findByRole('log');
}

const input = () => screen.getByRole('textbox', { name: AI_MESSAGES.questionLabel });
async function say(text: string) {
  await userEvent.type(input(), text);
  await userEvent.click(screen.getByRole('button', { name: AI_MESSAGES.send }));
}

afterEach(resetApi);

describe('«Spør mer» from the popover', () => {
  it('is shown only once an answer that says something is there', async () => {
    setUp(['error']);
    renderAt(detailPath(OLAS_HOME));
    await userEvent.click(await screen.findByRole('button', { name: `Spør KI om «${MUST.name}»` }));
    await screen.findByRole('alert');
    expect(screen.queryByRole('button', { name: AI_MESSAGES.askMore })).not.toBeInTheDocument();
  });

  it('pushes into the chat with the exchange and the Task as context', async () => {
    setUp(['ok']);
    const log = await escalate();
    expect(window.location.pathname).toBe(chatPath(OLAS_HOME));
    expect(screen.getByRole('heading', { name: AI_MESSAGES.chatLabel(MUST.name) })).toBeInTheDocument();
    expect(within(log).getByText(DEFAULT_Q)).toBeInTheDocument();
    expect(within(log).getByText(ANSWER)).toBeInTheDocument();
  });

  it('carries the user’s own question when that was what the popover asked', async () => {
    setUp(['ok', 'ok']);
    renderAt(detailPath(OLAS_HOME));
    await userEvent.click(await screen.findByRole('button', { name: `Spør KI om «${MUST.name}»` }));
    await screen.findByText(ANSWER);
    await userEvent.type(screen.getByRole('textbox', { name: AI_MESSAGES.questionLabel }), 'Hva med kalk?');
    await userEvent.click(screen.getByRole('button', { name: AI_MESSAGES.ask }));
    await userEvent.click(await screen.findByRole('button', { name: AI_MESSAGES.askMore }));
    const log = await screen.findByRole('log');
    expect(within(log).getByText('Hva med kalk?')).toBeInTheDocument();
    expect(within(log).queryByText(DEFAULT_Q)).not.toBeInTheDocument();
  });
});

describe('The chat', () => {
  it('sends the carried exchange as history with a follow-up, and shows the answer', async () => {
    const { bodies } = setUp(['ok']);
    const log = await escalate();
    await say('Og hvis det lukter?');
    await waitFor(() => expect(within(log).getAllByText(ANSWER)).toHaveLength(2));
    expect(bodies[1]).toEqual({
      question: 'Og hvis det lukter?',
      history: [
        { role: 'user', text: DEFAULT_Q },
        { role: 'assistant', text: ANSWER },
      ],
    });
    expect(within(log).getByText('Og hvis det lukter?')).toBeInTheDocument();
  });

  it('keeps growing the history message by message', async () => {
    const { bodies } = setUp(['ok']);
    const log = await escalate();
    await say('Første');
    await waitFor(() => expect(within(log).getAllByText(ANSWER)).toHaveLength(2));
    await say('Andre');
    await waitFor(() => expect(within(log).getAllByText(ANSWER)).toHaveLength(3));
    const history = (bodies[2] as { history: { role: string }[] }).history;
    expect(history.map((t) => t.role)).toEqual(['user', 'assistant', 'user', 'assistant']);
  });

  it('drops the oldest pairs past the server’s limit so the list still alternates', async () => {
    const { bodies } = setUp(['ok']);
    const log = await escalate();
    for (let i = 1; i <= 6; i += 1) {
      await say(`Spørsmål ${i}`);
      await waitFor(() => expect(within(log).getAllByText(ANSWER)).toHaveLength(i + 1));
    }
    const history = (bodies[6] as { history: { role: string; text: string }[] }).history;
    expect(history).toHaveLength(HISTORY_MAX_ENTRIES);
    expect(history[0]).toEqual({ role: 'user', text: 'Spørsmål 1' });
    expect(history.map((t) => t.role)).toEqual(Array.from({ length: 10 }, (_, i) => (i % 2 ? 'assistant' : 'user')));
  });

  it('starts empty on a direct link and sends the first message without history', async () => {
    const { bodies } = setUp(['ok']);
    renderAt(chatPath(OLAS_HOME));
    expect(await screen.findByText(AI_MESSAGES.chatEmpty(MUST.name))).toBeInTheDocument();
    // The disclaimer is there before any answer, from the fallback (AD-4: the server's text).
    expect(screen.getByText(FALLBACK_DISCLAIMER)).toBeVisible();
    await say('Hva med kalk?');
    expect(await screen.findByText(ANSWER)).toBeInTheDocument();
    expect(bodies).toEqual([{ question: 'Hva med kalk?' }]);
    expect(screen.queryByText(AI_MESSAGES.chatEmpty(MUST.name))).not.toBeInTheDocument();
  });

  it('shows the disclaimer outside the live region, and announces the stream politely', async () => {
    setUp(['demo']);
    const log = await escalate();
    const disclaimer = screen.getByText(DISCLAIMER);
    expect(disclaimer).toBeVisible();
    expect(log).toHaveAttribute('aria-live', 'polite');
    expect(log.contains(disclaimer)).toBe(false);
    expect(screen.getByText(AI_MESSAGES.demo)).toBeInTheDocument();
  });

  it('says the question goes to an external AI service when a real provider answered', async () => {
    setUp(['ok']);
    await escalate();
    expect(screen.getByText(AI_MESSAGES.external)).toBeInTheDocument();
  });

  it('shows a skeleton line, not a spinner, in the live region while it waits', async () => {
    setUp(['ok', 'slow']);
    const log = await escalate();
    await say('Mer?');
    const skeleton = await screen.findByTestId('answer-skeleton');
    expect(log.contains(skeleton)).toBe(true);
    expect(within(log).getByText('Mer?')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: AI_MESSAGES.send })).toBeDisabled();
    // The disclaimer of the answer already in hand stays visible meanwhile.
    expect(screen.getByText(DISCLAIMER)).toBeVisible();
  });

  it('does not send a blank message', async () => {
    const { bodies } = setUp(['ok']);
    await escalate();
    await say('   ');
    // The request would leave asynchronously, so give a wrongly sent one time to arrive.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(bodies).toHaveLength(1);
  });

  it('says plainly when the AI is unsure and keeps the disclaimer', async () => {
    setUp(['ok', 'low_confidence']);
    const log = await escalate();
    await say('Mer?');
    expect(await within(log).findByText(AI_MESSAGES.unsure)).toBeInTheDocument();
    expect(screen.getByText(DISCLAIMER)).toBeVisible();
  });

  it.each([['error' as const], ['network' as const], [500 as const]])(
    'keeps the failed message with a retry for %s, and a failed turn is never sent as history',
    async (outcome) => {
      const { bodies } = setUp(['ok', outcome, 'ok', 'ok']);
      const log = await escalate();
      await say('Mer?');
      expect(await within(log).findByRole('alert')).toHaveTextContent(AI_MESSAGES.failed);
      expect(within(log).getByText('Mer?')).toBeInTheDocument();
      await userEvent.click(screen.getByRole('button', { name: AI_MESSAGES.retry }));
      await waitFor(() => expect(within(log).getAllByText(ANSWER)).toHaveLength(2));
      expect(within(log).queryByRole('alert')).not.toBeInTheDocument();
      // The retry asks the same thing with the same history: the failed attempt left no turn.
      expect(bodies[2]).toEqual(bodies[1]);
      await say('Og så?');
      await waitFor(() => expect(bodies).toHaveLength(4));
      expect((bodies[3] as { history: unknown[] }).history).toHaveLength(4);
    },
  );

  it.each([['error' as const], ['network' as const], ['limit' as const]])(
    'keeps a disclaimer visible, outside the live region, when the very first message fails (%s)',
    async (outcome) => {
      setUp([outcome]);
      renderAt(chatPath(OLAS_HOME));
      await screen.findByText(AI_MESSAGES.chatEmpty(MUST.name));
      await say('Hei');
      await waitFor(() => expect(screen.queryByTestId('answer-skeleton')).not.toBeInTheDocument());
      const shown = screen.getByText(outcome === 'error' ? DISCLAIMER : FALLBACK_DISCLAIMER);
      expect(shown).toBeVisible();
      expect(screen.getByRole('log').contains(shown)).toBe(false);
    },
  );

  it('cuts an earlier answer longer than the server accepts, so the next message is not refused', async () => {
    const { bodies } = setUp(['ok']);
    renderAt(chatPath(OLAS_HOME));
    await screen.findByText(AI_MESSAGES.chatEmpty(MUST.name));
    const long = 'x'.repeat(HISTORY_ANSWER_MAX_LENGTH + 500);
    expect(historyOf([{ question: 'Q', answer: { status: 'ok', answer: long, disclaimer: DISCLAIMER, demo: false } }])[1].text).toHaveLength(
      HISTORY_ANSWER_MAX_LENGTH,
    );
    await say('Hei');
    expect(bodies).toHaveLength(1);
  });

  it('shows the default question with the same wording the server uses', () => {
    expect(defaultQuestion('Rens sluket')).toBe('Hvordan gjør jeg «Rens sluket»?');
  });

  it('says when the daily limit restarts in the stream, and keeps the conversation', async () => {
    setUp(['ok', 'limit']);
    const log = await escalate();
    await say('Mer?');
    const text = await within(log).findByText(/Du har brukt de 20 KI-spørsmålene dine i dag\./);
    expect(text).toHaveTextContent(`Du kan spørre igjen ${formatReset('2026-11-11T00:00:00Z')}.`);
    expect(within(log).getByText(ANSWER)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: AI_MESSAGES.retry })).not.toBeInTheDocument();
  });

  it('is there for a Tenant too', async () => {
    setUp(['ok'], OLAS_TENANCY);
    await escalate(OLAS_TENANCY);
    expect(screen.getByText(DISCLAIMER)).toBeVisible();
  });

  it('refetches the tasks on a 404 and shows nothing inline', async () => {
    const tasks = taskServer();
    const server = fakeApi({
      ...signedInWith(),
      [`GET /api/homes/${OLAS_HOME.id}/tasks`]: tasks.list,
      [`POST ${answerPath(OLAS_HOME, MUST)}`]: answerHandler([404]),
    });
    renderAt(chatPath(OLAS_HOME));
    await screen.findByText(AI_MESSAGES.chatEmpty(MUST.name));
    await say('Hei');
    await waitFor(() => expect(server.calls('GET', `/api/homes/${OLAS_HOME.id}/tasks`).length).toBeGreaterThan(1));
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows nothing inline on a 403 (the global handler routes)', async () => {
    setUp([403]);
    renderAt(chatPath(OLAS_HOME));
    await screen.findByText(AI_MESSAGES.chatEmpty(MUST.name));
    await say('Hei');
    await waitFor(() => expect(screen.queryByTestId('answer-skeleton')).not.toBeInTheDocument());
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: AI_MESSAGES.retry })).not.toBeInTheDocument();
  });

  it('links back to the Task', async () => {
    setUp(['ok']);
    renderAt(chatPath(OLAS_HOME));
    const back = await screen.findByRole('link', { name: AI_MESSAGES.backToTask(MUST.name) });
    expect(back).toHaveAttribute('href', detailPath(OLAS_HOME));
  });
});

describe('Guards', () => {
  it('sends a Task that is gone from the list back to the overview', async () => {
    fakeApi({ ...signedInWith() });
    renderAt(`/hjem/${OLAS_HOME.id}/oppgaver/00000000-0000-4000-8000-00000000dead/chat`);
    await waitFor(() => expect(window.location.pathname).toBe(`/hjem/${OLAS_HOME.id}`));
  });

  it('sends an unknown Home to the start', async () => {
    fakeApi({ ...signedInWith() });
    renderAt(`/hjem/00000000-0000-4000-8000-00000000dead/oppgaver/${MUST.id}/chat`);
    await waitFor(() => expect(window.location.pathname).not.toContain('/chat'));
  });
});

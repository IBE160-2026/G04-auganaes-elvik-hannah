// Story 5.1 (FR-14, AD-4, UX-DR48): the «?» on Task Detail. An inline popover, not a navigation:
// it asks at once with the server's default question, and a field asks something else. A skeleton
// line (not a spinner) while it waits, announced with aria-live="polite", and the answer the same
// way. The disclaimer and the line about the external AI service come with every answer. A failed
// or slow call is said plainly with a retry; nothing here touches completing the Task.
import { useId, useRef, useState, type FormEvent } from 'react';
import { AI_MESSAGES, AiLimitError, QUESTION_MAX_LENGTH, type Answer } from '../api/ai';
import { ApiError } from '../api/errors';
import { useAskTask } from '../api/queries';
import './QuickAnswer.css';

type QuickAnswerProps = { homeId: string; task: { id: string; name: string } };

export function QuickAnswer({ homeId, task }: QuickAnswerProps) {
  const ask = useAskTask(homeId);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState('');
  // The last question, so «Prøv igjen» asks the same thing.
  const lastQuestion = useRef<string | undefined>(undefined);
  const popoverId = useId();
  const inputId = useId();

  function send(question?: string) {
    lastQuestion.current = question;
    ask.mutate({ taskId: task.id, question });
  }

  function toggle() {
    const opening = !open;
    setOpen(opening);
    // Reopening keeps the answer: a call is only spent when there is nothing to show yet.
    if (opening && ask.isIdle) send();
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = draft.trim();
    if (question === '' || ask.isPending) return;
    send(question);
  }

  return (
    <section className="quick-answer">
      <button
        type="button"
        className="quick-answer__toggle"
        aria-expanded={open}
        aria-controls={popoverId}
        aria-label={`Spør KI om «${task.name}»`}
        onClick={toggle}
      >
        <span aria-hidden="true">?</span> Spør KI
      </button>
      <div id={popoverId} className="quick-answer__popover" hidden={!open}>
        <div className="quick-answer__result" aria-live="polite">
          {ask.isPending ? (
            <>
              <p className="quick-answer__visually-hidden">{AI_MESSAGES.loading}</p>
              <span className="quick-answer__skeleton" aria-hidden="true" data-testid="answer-skeleton" />
            </>
          ) : (
            <Result answer={ask.data} error={ask.error} onRetry={() => send(lastQuestion.current)} />
          )}
        </div>
        <form className="quick-answer__form" onSubmit={submit} noValidate>
          <label className="quick-answer__label" htmlFor={inputId}>
            {AI_MESSAGES.questionLabel}
          </label>
          <div className="quick-answer__row">
            <input
              id={inputId}
              type="text"
              className="quick-answer__input"
              maxLength={QUESTION_MAX_LENGTH}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
            />
            <button type="submit" className="quick-answer__ask" disabled={ask.isPending}>
              {AI_MESSAGES.ask}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

function Result({
  answer,
  error,
  onRetry,
}: {
  answer: Answer | undefined;
  error: Error | null;
  onRetry: () => void;
}) {
  if (error) {
    // 403 is the global handler's and 404 the Task guard's: nothing to say here.
    if (error instanceof ApiError && (error.status === 403 || error.status === 404)) return null;
    if (error instanceof AiLimitError) return <p className="quick-answer__text">{error.message}</p>;
    return <Failed onRetry={onRetry} />;
  }
  if (!answer) return null;
  return (
    <>
      {answer.status === 'error' ? (
        <Failed onRetry={onRetry} />
      ) : (
        <>
          {answer.status === 'low_confidence' && <p className="quick-answer__text">{AI_MESSAGES.unsure}</p>}
          <p className="quick-answer__answer">{answer.answer}</p>
        </>
      )}
      <p className="quick-answer__disclaimer">{answer.disclaimer}</p>
      <p className="quick-answer__note">{answer.demo ? AI_MESSAGES.demo : AI_MESSAGES.external}</p>
    </>
  );
}

function Failed({ onRetry }: { onRetry: () => void }) {
  return (
    <>
      <p className="quick-answer__text" role="alert">
        {AI_MESSAGES.failed}
      </p>
      <button type="button" className="quick-answer__retry" onClick={onRetry}>
        {AI_MESSAGES.retry}
      </button>
    </>
  );
}

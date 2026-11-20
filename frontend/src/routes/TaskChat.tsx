// Story 5.2 (FR-15, UX-DR9, NFR4): the AI chat at /hjem/<id>/oppgaver/<taskId>/chat, opened with
// «Spør mer» from the «?» popover. The conversation lives in this page only (the server stores
// none of it); each message sends the earlier completed exchanges again, and the Task comes from
// the path, so the AI keeps it as context. Every message is one AI call under the same timeout,
// data and daily-limit rules as «?». The disclaimer sits outside the live region and is always
// shown once an answer has arrived; new messages are announced politely.
// Guards as on Task Detail: an unknown Home goes to "/", a Home without Tasks or a Task that is
// gone goes back to the overview.
import { useId, useRef, useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useParams } from 'react-router';
import {
  AI_MESSAGES,
  AiLimitError,
  FALLBACK_DISCLAIMER,
  QUESTION_MAX_LENGTH,
  historyOf,
  type Answer,
  type Exchange,
} from '../api/ai';
import { ApiError } from '../api/errors';
import type { Home } from '../api/homes';
import { useAskTask, useHomes, useTasks } from '../api/queries';
import { TASK_MESSAGES } from '../api/tasks';
import { HomesLoadError } from './HomesLoadError';
import { useFocusOnMount } from './useFocusOnMount';
import './AuthForm.css';
import './TaskChat.css';

export function TaskChat() {
  const { homeId, taskId } = useParams();
  const homes = useHomes();

  if (homes.isPending) return <p role="status">Laster …</p>;
  if (!homes.data) return <HomesLoadError onRetry={() => void homes.refetch()} />;
  const home = homes.data.homes.find((h) => h.id === homeId);
  if (!home) return <Navigate to="/" replace />;
  if (!home.has_tasks) return <Navigate to={`/hjem/${home.id}`} replace />;
  return <TaskLoader key={home.id} home={home} taskId={taskId} />;
}

function TaskLoader({ home, taskId }: { home: Home; taskId: string | undefined }) {
  const tasks = useTasks(home.id);
  if (tasks.data) {
    const task = tasks.data.find((t) => t.id === taskId);
    if (!task) return <Navigate to={`/hjem/${home.id}`} replace />;
    return <Chat key={task.id} home={home} task={task} />;
  }
  if (tasks.isError) {
    // A 403 shows nothing inline: the global handler refetches and the guards route.
    if (tasks.error instanceof ApiError && tasks.error.status === 403) return null;
    return (
      <div className="task-chat">
        <p className="auth-form__error" role="alert">
          {TASK_MESSAGES.loadFailed}
        </p>
        <button type="button" className="task-chat__button" onClick={() => void tasks.refetch()}>
          {AI_MESSAGES.retry}
        </button>
        <Link to={`/hjem/${home.id}`} className="task-chat__link">
          Tilbake til oppgavene
        </Link>
      </div>
    );
  }
  return <p role="status">Laster …</p>;
}

/** The exchange «Spør mer» carried over, if the router state has the shape we put there. */
function carriedExchanges(state: unknown): Exchange[] {
  const list = (state as { exchanges?: unknown } | null)?.exchanges;
  if (!Array.isArray(list)) return [];
  return list.filter(
    (e): e is Exchange =>
      typeof e?.question === 'string' && typeof e?.answer?.answer === 'string' && typeof e?.answer?.disclaimer === 'string',
  );
}

function Chat({ home, task }: { home: Home; task: { id: string; name: string } }) {
  const titleRef = useFocusOnMount<HTMLHeadingElement>();
  const location = useLocation();
  const ask = useAskTask(home.id);
  const [exchanges, setExchanges] = useState<Exchange[]>(() => carriedExchanges(location.state));
  const [draft, setDraft] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();

  function send(question: string) {
    // Only completed exchanges go along as history; a failed message never does.
    ask.mutate(
      { taskId: task.id, question, history: historyOf(exchanges) },
      {
        onSuccess: (answer) => {
          if (answer.status !== 'error') setExchanges((all) => [...all, { question, answer }]);
        },
      },
    );
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = draft.trim();
    if (question === '' || ask.isPending) return;
    setDraft('');
    send(question);
    inputRef.current?.focus();
  }

  const asked = ask.variables?.question;
  const failed = ask.isError || ask.data?.status === 'error';
  // The newest answer in hand, a failed one included: its disclaimer is shown all the same.
  const newest: Answer | undefined = ask.data ?? exchanges.at(-1)?.answer;
  const disclaimer = newest?.disclaimer ?? FALLBACK_DISCLAIMER;
  const demo = newest?.demo;

  return (
    <div className="task-chat">
      <h1 ref={titleRef} tabIndex={-1} className="task-chat__title">
        {AI_MESSAGES.chatLabel(task.name)}
      </h1>
      <Link to={`/hjem/${home.id}/oppgaver/${task.id}`} className="task-chat__link">
        {AI_MESSAGES.backToTask(task.name)}
      </Link>
      <div className="task-chat__notes">
        <p className="task-chat__disclaimer">{disclaimer}</p>
        {newest && <p className="task-chat__note">{demo ? AI_MESSAGES.demo : AI_MESSAGES.external}</p>}
      </div>
      <div className="task-chat__stream" role="log" aria-live="polite" aria-label={AI_MESSAGES.chatLabel(task.name)}>
        {exchanges.length === 0 && !ask.isPending && !failed && (
          <p className="task-chat__empty">{AI_MESSAGES.chatEmpty(task.name)}</p>
        )}
        {exchanges.map((e, i) => (
          <Messages key={i} question={e.question} answer={e.answer} />
        ))}
        {ask.isPending && asked !== undefined && (
          <>
            <Message who="you" text={asked} />
            <p className="task-chat__visually-hidden">{AI_MESSAGES.loading}</p>
            <span className="task-chat__skeleton" aria-hidden="true" data-testid="answer-skeleton" />
          </>
        )}
        {failed && asked !== undefined && (
          <Failure
            question={asked}
            error={ask.error}
            onRetry={() => send(asked)}
          />
        )}
      </div>
      <form className="task-chat__form" onSubmit={submit} noValidate>
        <label className="task-chat__label" htmlFor={inputId}>
          {AI_MESSAGES.questionLabel}
        </label>
        <div className="task-chat__row">
          <input
            id={inputId}
            ref={inputRef}
            type="text"
            className="task-chat__input"
            maxLength={QUESTION_MAX_LENGTH}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <button type="submit" className="task-chat__button" disabled={ask.isPending}>
            {AI_MESSAGES.send}
          </button>
        </div>
      </form>
    </div>
  );
}

function Message({ who, text }: { who: 'you' | 'assistant'; text: string }) {
  return (
    <div className={`task-chat__message task-chat__message--${who}`}>
      <span className="task-chat__who">{AI_MESSAGES[who]}</span>
      <p className="task-chat__text">{text}</p>
    </div>
  );
}

function Messages({ question, answer }: { question: string; answer: Answer }) {
  return (
    <>
      <Message who="you" text={question} />
      {answer.status === 'low_confidence' && <p className="task-chat__unsure">{AI_MESSAGES.unsure}</p>}
      <Message who="assistant" text={answer.answer} />
    </>
  );
}

function Failure({ question, error, onRetry }: { question: string; error: Error | null; onRetry: () => void }) {
  // 403 is the global handler's and 404 the Task guard's: nothing to say here.
  if (error instanceof ApiError && (error.status === 403 || error.status === 404)) return null;
  return (
    <>
      <Message who="you" text={question} />
      {error instanceof AiLimitError ? (
        <p className="task-chat__unsure">{error.message}</p>
      ) : (
        <>
          <p className="task-chat__unsure" role="alert">
            {AI_MESSAGES.failed}
          </p>
          <button type="button" className="task-chat__button task-chat__retry" onClick={onRetry}>
            {AI_MESSAGES.retry}
          </button>
        </>
      )}
    </>
  );
}

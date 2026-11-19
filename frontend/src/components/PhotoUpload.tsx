// Story 4.2 (FR-18, FR-19, AD-11): a Tenant completes a task that requires Photo Evidence by
// uploading a photo (camera or file picker). Pessimistic: «Laster opp …» until the server has
// answered, and only then does the task show as done (the list is replaced by the server's Task).
// A failure shows the message with «Prøv igjen» at the control, keeping the chosen file. The
// server writes the accessible description; nothing here asks for one or shows a filename.
import { useRef, useState, type ChangeEvent } from 'react';
import { ApiError } from '../api/errors';
import type { Home } from '../api/homes';
import { PHOTO_UPLOAD_MESSAGES } from '../api/photoEvidence';
import { useUploadPhotoEvidence, type TaskView } from '../api/queries';
import './PhotoUpload.css';

export function PhotoUpload({ home, task }: { home: Home; task: TaskView }) {
  const upload = useUploadPhotoEvidence(home.id);
  const chosen = useRef<File | null>(null);
  const [done, setDone] = useState(false);

  function send(file: File) {
    chosen.current = file;
    upload.mutate({ task, file }, { onSuccess: () => setDone(true) });
  }

  function onChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) send(file);
    // The same file can be picked again after a failure.
    event.target.value = '';
  }

  // The control and its note only while the task is open. The component stays mounted when the
  // server's answer completes the task, so the result below is still announced.
  const open = !task.completion && !task.pending;
  if (!open && !done) return null;

  // A 403 shows nothing inline: the global handler refetches and the guards route.
  const failure =
    upload.error instanceof ApiError && upload.error.status === 403 ? null : (upload.error?.message ?? null);
  const retryable = !(upload.error instanceof ApiError && [409, 413, 415].includes(upload.error.status));

  return (
    <section className="photo-upload" aria-labelledby={`photo-upload-${task.id}`}>
      <h2 id={`photo-upload-${task.id}`} className="photo-upload__title">
        Bildebevis
      </h2>
      {!done && (
        <p className="photo-upload__note">
          Utleieren krever et bilde for å fullføre denne oppgaven. Oppgaven er fullført med en
          gang bildet er lastet opp.
        </p>
      )}
      {!done && (
        <label className="photo-upload__pick">
          <span>Ta eller velg bilde</span>
          <input
            type="file"
            accept="image/*"
            disabled={upload.isPending}
            onChange={onChange}
          />
        </label>
      )}
      {failure && (
        <>
          <p className="auth-form__error" role="alert">
            {failure}
          </p>
          {retryable && chosen.current && (
            <button type="button" className="photo-upload__retry" onClick={() => send(chosen.current as File)}>
              Prøv igjen
            </button>
          )}
        </>
      )}
      {/* Always in the DOM, so the progress and the result are announced when they arrive. */}
      <p className="photo-upload__status" aria-live="polite">
        {upload.isPending ? PHOTO_UPLOAD_MESSAGES.uploading : done ? PHOTO_UPLOAD_MESSAGES.done : ''}
      </p>
    </section>
  );
}

// Story 4.3 (FR-19, NFR5): the Landlord reviews the current photo of a Task on Task Detail. The
// server writes the description and the time; the browser formats no date. The photo is fetched
// through the API (it needs the Bearer token) and shown from a data address made in the browser.
// Nothing here offers download, history or deleting.
import { ApiError } from '../api/errors';
import type { Home } from '../api/homes';
import { PHOTO_VIEW_MESSAGES } from '../api/photoEvidence';
import { usePhotoEvidence, type TaskView } from '../api/queries';
import './PhotoEvidenceView.css';

export function PhotoEvidenceView({ home, task }: { home: Home; task: TaskView }) {
  const { info, image } = usePhotoEvidence(home.id, task.id, true);
  const evidence = info.data;
  const url = image.data;

  // A 404 on the image is final (the stored file is gone): its message, no retry.
  const gone = image.error instanceof ApiError && image.error.status === 404;
  const failed = info.isError || (image.isError && !gone);
  // A Task that cannot have a photo and has none shows nothing; a required one says so.
  if (!failed && !info.isPending && !evidence && !task.requires_photo_evidence) return null;

  return (
    <section className="photo-view" aria-labelledby={`photo-view-${task.id}`}>
      <h2 id={`photo-view-${task.id}`} className="photo-view__title">
        Bildebevis
      </h2>
      {info.isPending && <p role="status">Laster …</p>}
      {!info.isPending && !failed && !evidence && <p className="photo-view__note">{PHOTO_VIEW_MESSAGES.none}</p>}
      {evidence && (
        <>
          <p className="photo-view__note">{evidence.description}</p>
          {image.isPending && <p role="status">Laster bildet …</p>}
          {url && <img className="photo-view__image" src={url} alt={PHOTO_VIEW_MESSAGES.alt} />}
        </>
      )}
      {gone && !failed && (
        <p className="auth-form__error" role="alert">
          {image.error?.message}
        </p>
      )}
      {failed && (
        <>
          <p className="auth-form__error" role="alert">
            {PHOTO_VIEW_MESSAGES.failed}
          </p>
          <button
            type="button"
            className="photo-view__retry"
            onClick={() => {
              void (info.isError ? info.refetch() : image.refetch());
            }}
          >
            Prøv igjen
          </button>
        </>
      )}
    </section>
  );
}

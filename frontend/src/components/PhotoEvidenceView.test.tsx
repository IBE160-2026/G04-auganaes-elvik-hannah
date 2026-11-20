// Story 4.3 (FR-19, AD-5, NFR5): the Landlord sees the current photo on Task Detail. The photo is
// fetched through the API with the Bearer token and shown from a data address; a Tenant gets no
// view and no request.
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import type { Task } from '../api/tasks';
import {
  OLAS_TASKS,
  OLAS_TENANCY,
  fakeApi,
  json,
  resetApi,
  signedInWith,
  tasksPath,
} from '../test-utils/fakeApi';

const LANDLORD_HOME = { ...OLAS_TENANCY, role: 'landlord' as const, can_adjust_tasks: true };
const REQUIRED: Task = { ...OLAS_TASKS[0], requires_photo_evidence: true, may_require_photo_evidence: true };
const TASKS = [REQUIRED, ...OLAS_TASKS.slice(1)];
const evidencePath = `${tasksPath(LANDLORD_HOME)}/${REQUIRED.id}/photo-evidence`;
const detailUrl = `/hjem/${LANDLORD_HOME.id}/oppgaver/${REQUIRED.id}`;
const DESCRIPTION = 'Bildebevis lastet opp av Martin, 29. sep';

function renderAt(url: string) {
  window.history.pushState({}, '', url);
  return render(<App />);
}

function landlordServer(extra: Record<string, (request: Request) => Response | Promise<Response>> = {}) {
  return fakeApi({
    ...signedInWith([LANDLORD_HOME]),
    [`GET ${tasksPath(LANDLORD_HOME)}`]: () => json(200, { tasks: TASKS }),
    ...extra,
  });
}

afterEach(resetApi);

describe('Photo Evidence view', () => {
  it('shows the photo with the server\'s description as its text, fetched with the Bearer token', async () => {
    const seen: (string | null)[] = [];
    landlordServer({
      [`GET ${evidencePath}`]: () => json(200, { evidence: { description: DESCRIPTION, uploaded_at: '2026-09-29T10:00:00Z' } }),
      [`GET ${evidencePath}/image`]: (request) => {
        seen.push(request.headers.get('Authorization'));
        return new Response(new Uint8Array([0xff, 0xd8, 0xff]), { headers: { 'Content-Type': 'image/jpeg' } });
      },
    });
    renderAt(detailUrl);

    const image = await screen.findByRole('img', { name: 'Bildebevis for oppgaven' });
    // Guards the data address: no storage address ever reaches the browser, only bytes it made itself.
    expect(image.getAttribute('src')).toMatch(/^data:image\/jpeg;base64,/);
    expect(seen[0]).toMatch(/^Bearer /);
  });

  it('says no photo has been uploaded when the server answers evidence null', async () => {
    landlordServer({ [`GET ${evidencePath}`]: () => json(200, { evidence: null }) });
    renderAt(detailUrl);

    // Guards `!evidence && task.requires_photo_evidence`: a required task with no photo says so.
    expect(await screen.findByText('Ingen bilde er lastet opp ennå.')).toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('shows a retry when the photo cannot be fetched, and the retry loads it', async () => {
    let fail = true;
    landlordServer({
      [`GET ${evidencePath}`]: () => json(200, { evidence: { description: DESCRIPTION, uploaded_at: '2026-09-29T10:00:00Z' } }),
      [`GET ${evidencePath}/image`]: () =>
        fail ? json(503, { detail: 'Vi fikk ikke hentet bildet. Prøv igjen.' }) : new Response(new Uint8Array([0xff, 0xd8, 0xff])),
    });
    renderAt(detailUrl);

    // Guards `failed`: the message and the retry at the control, never a blank gap.
    expect(await screen.findByRole('alert')).toHaveTextContent('Vi fikk ikke hentet bildet.');
    fail = false;
    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));
    expect(await screen.findByRole('img', { name: 'Bildebevis for oppgaven' })).toBeInTheDocument();
  });

  it('says the photo is gone, with no retry, when the stored file is missing', async () => {
    landlordServer({
      [`GET ${evidencePath}`]: () => json(200, { evidence: { description: DESCRIPTION, uploaded_at: '2026-09-29T10:00:00Z' } }),
      [`GET ${evidencePath}/image`]: () => json(404, { detail: 'Bildet finnes ikke lenger.' }),
    });
    renderAt(detailUrl);

    // Guards `gone`: a permanent 404 shows the server's reason and no «Prøv igjen» that cannot succeed.
    expect(await screen.findByRole('alert')).toHaveTextContent('Bildet finnes ikke lenger.');
    expect(screen.queryByRole('button', { name: 'Prøv igjen' })).not.toBeInTheDocument();
  });

  it('makes no request and shows nothing to a Tenant', async () => {
    let asked = false;
    fakeApi({
      ...signedInWith([OLAS_TENANCY]),
      [`GET ${tasksPath(OLAS_TENANCY)}`]: () => json(200, { tasks: TASKS }),
      [`GET ${tasksPath(OLAS_TENANCY)}/${REQUIRED.id}/photo-evidence`]: () => {
        asked = true;
        return json(403, { detail: 'nei' });
      },
    });
    renderAt(`/hjem/${OLAS_TENANCY.id}/oppgaver/${REQUIRED.id}`);

    await screen.findByRole('heading', { name: REQUIRED.name });
    // Guards `home.role === 'landlord'`: the view is the Landlord's only (NFR6).
    expect(asked).toBe(false);
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });
});

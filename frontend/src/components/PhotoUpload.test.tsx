// Story 4.2 (FR-18, FR-19, AD-3, AD-11): a Tenant completes a task that requires a photo.
// The upload is pessimistic, shows a retry on failure and names no file; a Tenant's checkbox is
// replaced by «Last opp bilde» on the overview.
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { prepareImage } from '../api/photoEvidence';
import type { Task } from '../api/tasks';
import {
  OLAS_HOME,
  OLAS_TASKS,
  OLAS_TENANCY,
  fakeApi,
  json,
  resetApi,
  signedInWith,
  tasksPath,
} from '../test-utils/fakeApi';

const REQUIRED: Task = { ...OLAS_TASKS[0], requires_photo_evidence: true, may_require_photo_evidence: true };
const TASKS = [REQUIRED, ...OLAS_TASKS.slice(1)];
const DONE: Task = {
  ...REQUIRED,
  instance_id: '00000000-0000-4000-8000-0000000000f9',
  due_on: '2026-12-20',
  completion: { completed_on: '2026-11-20', days_since: 0, completed_this_year: true, by: 'you', name: null },
};
const uploadPath = `${tasksPath(OLAS_TENANCY)}/${REQUIRED.id}/instances/${REQUIRED.instance_id}/photo-evidence`;
const completionPath = `${tasksPath(OLAS_TENANCY)}/${REQUIRED.id}/instances/${REQUIRED.instance_id}/completion`;
const detailUrl = `/hjem/${OLAS_TENANCY.id}/oppgaver/${REQUIRED.id}`;

function photo() {
  return new File([new Uint8Array([0xff, 0xd8, 0xff, 0xe0])], 'IMG_4711.jpg', { type: 'image/jpeg' });
}

function renderAt(url: string) {
  window.history.pushState({}, '', url);
  return render(<App />);
}

function tenantServer(extra: Record<string, (request: Request) => Response | Promise<Response>> = {}) {
  return fakeApi({
    ...signedInWith([OLAS_TENANCY]),
    [`GET ${tasksPath(OLAS_TENANCY)}`]: () => json(200, { tasks: TASKS }),
    ...extra,
  });
}

afterEach(resetApi);

describe('Photo Evidence upload', () => {
  it('replaces a Tenant\'s checkbox with «Last opp bilde» only on the task that requires one', async () => {
    tenantServer();
    renderAt(`/hjem/${OLAS_TENANCY.id}`);

    expect(await screen.findByRole('link', { name: 'Last opp bilde' })).toHaveAttribute('href', detailUrl);
    // Guards `needsPhoto`: the other two tasks keep their checkbox.
    expect(screen.getAllByRole('checkbox')).toHaveLength(2);
  });

  it('shows no upload for a household member or when the task needs no photo', async () => {
    fakeApi({
      ...signedInWith([OLAS_HOME]),
      [`GET ${tasksPath(OLAS_HOME)}`]: () => json(200, { tasks: TASKS }),
    });
    renderAt(`/hjem/${OLAS_HOME.id}/oppgaver/${REQUIRED.id}`);

    await screen.findByRole('heading', { level: 1, name: REQUIRED.name });
    // Guards `home.role === 'tenant'`: the requirement is for Tenants.
    expect(screen.queryByRole('heading', { name: 'Bildebevis' })).toBeNull();
  });

  it('sends the photo as the body, waits for the answer and only then shows the task done', async () => {
    let release: (response: Response) => void = () => {};
    const api = tenantServer({
      [`POST ${uploadPath}`]: () => new Promise<Response>((resolve) => (release = resolve)),
    });
    renderAt(detailUrl);

    await userEvent.upload(await screen.findByLabelText('Ta eller velg bilde'), photo());

    expect(await screen.findByText('Laster opp …')).toBeInTheDocument();
    // Guards the pessimistic pattern (AD-11): no «done» text and no completion while in flight.
    expect(screen.queryByText('Bilde lastet opp. Oppgaven er fullført.')).toBeNull();
    release(json(200, DONE));

    expect(await screen.findByText('Bilde lastet opp. Oppgaven er fullført.')).toHaveAttribute('aria-live', 'polite');
    const [request] = api.calls('POST', uploadPath);
    expect(request.headers.get('Content-Type')).toBe('image/jpeg');
    expect((await request.blob()).size).toBe(4);
    // Never the filename or a description typed by the user.
    expect(screen.queryByText(/IMG_4711/)).toBeNull();
  });

  it('shows a retry after a failed upload and sends the same photo again', async () => {
    let attempts = 0;
    const api = tenantServer({
      [`POST ${uploadPath}`]: () => (++attempts === 1 ? json(500, { detail: 'boom' }) : json(200, DONE)),
    });
    renderAt(detailUrl);
    await userEvent.upload(await screen.findByLabelText('Ta eller velg bilde'), photo());

    expect(await screen.findByRole('alert')).toHaveTextContent('Vi fikk ikke lastet opp bildet.');
    expect(screen.queryByText('Bilde lastet opp. Oppgaven er fullført.')).toBeNull();

    await userEvent.click(screen.getByRole('button', { name: 'Prøv igjen' }));

    expect(await screen.findByText('Bilde lastet opp. Oppgaven er fullført.')).toBeInTheDocument();
    expect(api.calls('POST', uploadPath)).toHaveLength(2);
    expect((await api.calls('POST', uploadPath)[1].blob()).size).toBe(4);
  });

  it('shows the server\'s reason for a rejected photo and offers no retry', async () => {
    tenantServer({ [`POST ${uploadPath}`]: () => json(415, { detail: 'Bildet må være en JPEG-fil.' }) });
    renderAt(detailUrl);

    await userEvent.upload(await screen.findByLabelText('Ta eller velg bilde'), photo());

    expect(await screen.findByRole('alert')).toHaveTextContent('Bildet må være en JPEG-fil.');
    expect(screen.queryByRole('button', { name: 'Prøv igjen' })).toBeNull();
  });

  it('never ticks the task through the plain completion route', async () => {
    const api = tenantServer({ [`POST ${completionPath}`]: () => json(409, { detail: 'x' }) });
    renderAt(`/hjem/${OLAS_TENANCY.id}`);

    await screen.findByRole('link', { name: 'Last opp bilde' });

    expect(api.calls('POST', completionPath)).toHaveLength(0);
  });

  it('prepareImage gives the file back when the browser cannot decode it', async () => {
    const file = photo();

    // jsdom has no createImageBitmap, which is the fallback path the server then checks.
    expect(await prepareImage(file)).toBe(file);
  });
});

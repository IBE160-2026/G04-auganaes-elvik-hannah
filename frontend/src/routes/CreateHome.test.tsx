// Story 1.3 (FR-1, FR-3): the Create Home form, its inline errors and the landing after create.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { HOME_MESSAGES, type Home } from '../api/homes';
import { OLAS_HOME, fakeApi, homesResponse, json, resetApi, signedInWith } from '../test-utils/fakeApi';

const RENTAL: Home = { ...OLAS_HOME, name: 'Storgata 1', type: 'landlord', role: 'landlord' };

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

async function fillName(name: string) {
  await userEvent.type(await screen.findByLabelText('Navn på hjemmet'), name);
}

function submit() {
  return userEvent.click(screen.getByRole('button', { name: 'Opprett hjem' }));
}

afterEach(resetApi);

describe('Create Home', () => {
  it('creates a Household Home and lands on it without bouncing back', async () => {
    let created = false;
    const server = fakeApi({
      ...signedInWith([], ['household', 'landlord']),
      // After the create, the refetch never answers: only the cache write can show the Home.
      'GET /api/homes': () =>
        created ? new Promise<Response>(() => {}) : json(200, homesResponse([], ['household', 'landlord'])),
      'POST /api/homes': () => {
        created = true;
        return json(201, OLAS_HOME);
      },
    });
    renderAt('/');

    await userEvent.click(await screen.findByRole('radio', { name: /Husstand/ }));
    await fillName('  Kollektivet ');
    await submit();

    expect(await screen.findByRole('heading', { name: 'Kollektivet' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
    const [request] = server.calls('POST', '/api/homes');
    expect(await request.json()).toEqual({ name: 'Kollektivet', type: 'household' });
  });

  it('asks for a type before sending, with focus on the choice', async () => {
    const server = fakeApi(signedInWith([], ['household', 'landlord']));
    renderAt('/nytt-hjem');

    await fillName('Kollektivet');
    await submit();

    const [household, landlord] = screen.getAllByRole('radio');
    await waitFor(() => expect(household).toHaveFocus());
    expect(household).toHaveAttribute('aria-invalid', 'true');
    expect(landlord).toHaveAccessibleDescription(HOME_MESSAGES.typeMissing);
    expect(server.calls('POST', '/api/homes')).toHaveLength(0);
  });

  it('asks for a name before sending', async () => {
    const server = fakeApi(signedInWith([], ['household', 'landlord']));
    renderAt('/nytt-hjem');

    await userEvent.click(await screen.findByRole('radio', { name: /Utleiebolig/ }));
    await fillName('   ');
    await submit();

    const name = screen.getByLabelText('Navn på hjemmet');
    await waitFor(() => expect(name).toHaveFocus());
    expect(name).toHaveAccessibleDescription(expect.stringContaining(HOME_MESSAGES.nameMissing));
    expect(server.calls('POST', '/api/homes')).toHaveLength(0);
  });

  it('shows a 409 inline at the action, in the server\'s words, and refetches the allowed types', async () => {
    const detail = 'Du er allerede med i et hjem, og du kan bare være med i ett hjem om gangen.';
    const server = fakeApi({ ...signedInWith([], ['household', 'landlord']), 'POST /api/homes': () => json(409, { detail }) });
    renderAt('/nytt-hjem');

    await userEvent.click(await screen.findByRole('radio', { name: /Husstand/ }));
    await fillName('Kollektivet');
    await submit();

    expect(await screen.findByRole('alert')).toHaveTextContent(detail);
    expect(window.location.pathname).toBe('/nytt-hjem');
    await waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(2));
  });

  it('after a 409, sends a user who may no longer create anything to their Home', async () => {
    let conflicted = false;
    fakeApi({
      ...signedInWith([], ['household', 'landlord']),
      // A Home was made in another tab: the server now has it and allows nothing more.
      'GET /api/homes': () =>
        json(200, conflicted ? homesResponse([OLAS_HOME], []) : homesResponse([], ['household', 'landlord'])),
      'POST /api/homes': () => {
        conflicted = true;
        return json(409, { detail: 'Du er allerede med i et hjem.' });
      },
    });
    renderAt('/nytt-hjem');

    await userEvent.click(await screen.findByRole('radio', { name: /Husstand/ }));
    await fillName('Kollektivet');
    await submit();

    expect(await screen.findByRole('heading', { name: OLAS_HOME.name })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
  });

  it('shows a server 422 on the name field', async () => {
    fakeApi({
      ...signedInWith([], ['household', 'landlord']),
      'POST /api/homes': () =>
        json(422, { detail: [{ loc: ['body', 'name'], msg: 'x', type: 'string_too_long' }] }),
    });
    renderAt('/nytt-hjem');

    await userEvent.click(await screen.findByRole('radio', { name: /Husstand/ }));
    await fillName('Kollektivet');
    await submit();

    await waitFor(() =>
      expect(screen.getByLabelText('Navn på hjemmet')).toHaveAccessibleDescription(
        expect.stringContaining(HOME_MESSAGES.nameTooLong),
      ),
    );
  });

  it('gives a Landlord with Homes only the name field and creates a Landlord Home', async () => {
    const second = { ...RENTAL, id: '00000000-0000-4000-8000-0000000000b2', name: 'Storgata 2' };
    let created = false;
    const server = fakeApi({
      ...signedInWith([RENTAL], ['landlord']),
      'GET /api/homes': () => json(200, homesResponse(created ? [second, RENTAL] : [RENTAL], ['landlord'])),
      'POST /api/homes': () => {
        created = true;
        return json(201, second);
      },
    });
    renderAt('/nytt-hjem');

    expect(await screen.findByRole('heading', { name: 'Opprett ny utleiebolig' })).toBeInTheDocument();
    expect(screen.queryByRole('radio')).not.toBeInTheDocument();
    await fillName('Storgata 2');
    await submit();

    expect(await screen.findByRole('heading', { name: 'Storgata 2' })).toBeInTheDocument();
    expect(window.location.pathname).toBe('/');
    const [request] = server.calls('POST', '/api/homes');
    expect(await request.json()).toEqual({ name: 'Storgata 2', type: 'landlord' });
  });
});

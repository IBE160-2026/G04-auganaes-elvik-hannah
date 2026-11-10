// Story 1.3 (FR-1, FR-3): the Create Home form, its inline errors and the landing after create.
// Story 2.1: a created Home goes on to Task Setup, and Back cannot reach the form again.
// Story 1.9 (issue #30): the title and lead per case, and the matrix rows the frontend sees.
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { HOME_MESSAGES, type Home } from '../api/homes';
import { OLAS_HOME, fakeApi, homesResponse, json, resetApi, signedInWith } from '../test-utils/fakeApi';

const RENTAL: Home = { ...OLAS_HOME, name: 'Storgata 1', type: 'landlord', role: 'landlord', can_leave: false };
// As POST /api/homes returns it: a new Home has no Tasks yet.
const NEW_HOME: Home = { ...OLAS_HOME, has_tasks: false };

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
  it('creates a Household Home and goes on to Task Setup without bouncing back', async () => {
    let created = false;
    const server = fakeApi({
      ...signedInWith([], ['household', 'landlord']),
      // After the create, the refetch never answers: only the cache write can show the Home.
      'GET /api/homes': () =>
        created ? new Promise<Response>(() => {}) : json(200, homesResponse([], ['household', 'landlord'])),
      'POST /api/homes': () => {
        created = true;
        return json(201, NEW_HOME);
      },
    });
    renderAt('/');

    await userEvent.click(await screen.findByRole('radio', { name: /Husstand/ }));
    await fillName('  Kollektivet ');
    const entries = window.history.length;
    await submit();

    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${NEW_HOME.id}/oppgaveoppsett`);
    // replace: Create Home is not left behind in the history, so Back cannot make a second Home.
    expect(window.history.length).toBe(entries);
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
    const detail = 'Du er allerede med i «Karis». Du kan bare være med i ett hjem om gangen.';
    const server = fakeApi({ ...signedInWith([], ['household', 'landlord']), 'POST /api/homes': () => json(409, { detail }) });
    renderAt('/nytt-hjem');

    await userEvent.click(await screen.findByRole('radio', { name: /Husstand/ }));
    await fillName('Kollektivet');
    await submit();

    expect(await screen.findByRole('alert')).toHaveTextContent(detail);
    expect(window.location.pathname).toBe('/nytt-hjem');
    await waitFor(() => expect(server.calls('GET', '/api/homes')).toHaveLength(2));
  });

  it('after a 409, offers only a Landlord Home and names the Home the user now lives in', async () => {
    let conflicted = false;
    const detail = 'Du er allerede med i «Kollektivet». Du kan bare være med i ett hjem om gangen.';
    fakeApi({
      ...signedInWith([], ['household', 'landlord']),
      // A Home was joined in another tab: the server now offers only a Landlord Home.
      'GET /api/homes': () =>
        json(
          200,
          conflicted
            ? homesResponse([OLAS_HOME], ['landlord'], OLAS_HOME.id)
            : homesResponse([], ['household', 'landlord']),
        ),
      'POST /api/homes': () => {
        conflicted = true;
        return json(409, { detail });
      },
    });
    renderAt('/nytt-hjem');

    await userEvent.click(await screen.findByRole('radio', { name: /Husstand/ }));
    await fillName('Kollektivet');
    await submit();

    expect(await screen.findByRole('heading', { name: 'Opprett ny utleiebolig' })).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(detail);
    expect(screen.queryByRole('radio')).not.toBeInTheDocument();
    // The name must be typed again, so one more tap cannot create a type never chosen.
    expect(screen.getByLabelText('Navn på hjemmet')).toHaveValue('');
    expect(window.location.pathname).toBe('/nytt-hjem');
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

  it('offers a Landlord who lives in no Home both types and creates her Household Home', async () => {
    let created = false;
    const server = fakeApi({
      ...signedInWith([RENTAL], ['household', 'landlord']),
      'GET /api/homes': () =>
        json(
          200,
          created
            ? homesResponse([NEW_HOME, RENTAL], ['landlord'], NEW_HOME.id)
            : homesResponse([RENTAL], ['household', 'landlord']),
        ),
      'POST /api/homes': () => {
        created = true;
        return json(201, NEW_HOME);
      },
    });
    renderAt('/nytt-hjem');

    expect(await screen.findByRole('heading', { name: 'Opprett nytt hjem' })).toBeInTheDocument();
    // No first-Home lead and no lead about a Membership: Kari lives in no Home.
    expect(screen.queryByText(/Velg det som passer/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Du blir utleier/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('radio', { name: /Husstand/ }));
    await fillName('Karis');
    await submit();

    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${NEW_HOME.id}/oppgaveoppsett`);
    const [request] = server.calls('POST', '/api/homes');
    expect(await request.json()).toEqual({ name: 'Karis', type: 'household' });
  });

  it('gives a Household Member only the name field, the lead naming her Home, and creates a Landlord Home', async () => {
    const rental = { ...RENTAL, id: '00000000-0000-4000-8000-0000000000b2', name: 'Storgata 2', has_tasks: false };
    let created = false;
    const server = fakeApi({
      ...signedInWith([OLAS_HOME], ['landlord'], OLAS_HOME.id),
      'GET /api/homes': () =>
        json(200, homesResponse(created ? [rental, OLAS_HOME] : [OLAS_HOME], ['landlord'], OLAS_HOME.id)),
      'POST /api/homes': () => {
        created = true;
        return json(201, rental);
      },
    });
    renderAt('/nytt-hjem');

    expect(await screen.findByRole('heading', { name: 'Opprett ny utleiebolig' })).toBeInTheDocument();
    expect(
      screen.getByText('Du blir utleier for den nye boligen. Medlemskapet ditt i «Kollektivet» endres ikke.'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('radio')).not.toBeInTheDocument();
    await fillName('Storgata 2');
    await submit();

    // Story 2.1: a Landlord Home without Tenants is set up too.
    expect(await screen.findByRole('heading', { name: 'Sett opp oppgaver' })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/hjem/${rental.id}/oppgaveoppsett`);
    const [request] = server.calls('POST', '/api/homes');
    expect(await request.json()).toEqual({ name: 'Storgata 2', type: 'landlord' });
  });
});

// Story 3.1 (FR-10, AD-12): the service worker shows a pushed message and opens only app paths.
// The worker is a classic script that registers its handlers on `self`, which is `window` here.
const showNotification = vi.fn().mockResolvedValue(undefined);
const openWindow = vi.fn().mockResolvedValue(null);
const listeners = new Map<string, EventListener>();

beforeAll(async () => {
  const add = window.addEventListener.bind(window);
  vi.spyOn(window, 'addEventListener').mockImplementation((type, listener, options) => {
    if (['push', 'notificationclick'].includes(type) && typeof listener === 'function') {
      listeners.set(type, listener as EventListener);
    }
    add(type, listener, options);
  });
  Object.assign(window, { registration: { showNotification }, clients: { openWindow } });
  // By variable, so TypeScript does not pull the worker's webworker lib into the app's program.
  const worker = './service-worker';
  await import(/* @vite-ignore */ worker);
});

beforeEach(() => {
  showNotification.mockClear();
  openWindow.mockClear();
});

function pushEvent(data: { json: () => unknown } | null) {
  const waits: Promise<unknown>[] = [];
  const event = Object.assign(new Event('push'), { data, waitUntil: (p: Promise<unknown>) => waits.push(p) });
  listeners.get('push')!(event);
  return Promise.all(waits);
}

function clickEvent(data: unknown) {
  const close = vi.fn();
  const waits: Promise<unknown>[] = [];
  const event = Object.assign(new Event('notificationclick'), {
    notification: { close, data },
    waitUntil: (p: Promise<unknown>) => waits.push(p),
  });
  listeners.get('notificationclick')!(event);
  return { close, done: Promise.all(waits) };
}

describe('push handler', () => {
  it('shows the title and body from the payload and keeps its in-app link', async () => {
    await pushEvent({ json: () => ({ title: 'Forfalt', body: 'Rens sluket', url: '/hjem/1' }) });
    expect(showNotification).toHaveBeenCalledWith('Forfalt', { body: 'Rens sluket', data: { url: '/hjem/1' } });
  });

  it('still shows a notification when the payload is empty or not JSON', async () => {
    await pushEvent(null);
    await pushEvent({
      json: () => {
        throw new SyntaxError('bad');
      },
    });
    expect(showNotification).toHaveBeenCalledTimes(2);
    expect(showNotification).toHaveBeenLastCalledWith('Husly', { body: undefined, data: { url: '/' } });
  });

  it('never carries a link that leaves the app', async () => {
    await pushEvent({ json: () => ({ title: 'x', url: 'https://evil.example/' }) });
    await pushEvent({ json: () => ({ title: 'x', url: '//evil.example/' }) });
    // A backslash counts as a slash in a browser, so this one also leaves the app.
    await pushEvent({ json: () => ({ title: 'x', url: '/\\evil.example' }) });
    expect(showNotification).toHaveBeenCalledTimes(3);
    for (const call of showNotification.mock.calls) expect(call[1].data.url).toBe('/');
  });
});

describe('notificationclick handler', () => {
  it('closes the notification and opens its link', async () => {
    const { close, done } = clickEvent({ url: '/hjem/1/oppgaver/2' });
    await done;
    expect(close).toHaveBeenCalled();
    expect(openWindow).toHaveBeenCalledWith('/hjem/1/oppgaver/2');
  });

  it('opens the root for a missing or foreign link', async () => {
    await clickEvent(undefined).done;
    await clickEvent({ url: 'https://evil.example/' }).done;
    await clickEvent({ url: '/\\evil.example' }).done;
    expect(openWindow.mock.calls).toEqual([['/'], ['/'], ['/']]);
  });
});

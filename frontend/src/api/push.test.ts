// Story 3.1 (UX-DR31): the blocked-push note is dismissed once per user and device.
import { readNoteDismissed, readPushStatus, recordNoteDismissed } from './push';

describe('blocked-push note dismissal', () => {
  it('is remembered for the user who closed it, not for another user on the same device', () => {
    expect(readNoteDismissed('ola')).toBe(false);
    recordNoteDismissed('ola');
    expect(readNoteDismissed('ola')).toBe(true);
    expect(readNoteDismissed('mari')).toBe(false);
  });

  it('counts as not dismissed when storage throws, so the note errs on the side of showing', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError');
    });
    expect(readNoteDismissed('ola')).toBe(false);
    vi.restoreAllMocks();
  });
});

describe('readPushStatus', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    delete (navigator as { serviceWorker?: unknown }).serviceWorker;
  });

  it('answers «unsupported» instead of rejecting when the registration lookup throws', async () => {
    vi.stubGlobal('Notification', { permission: 'default' });
    vi.stubGlobal('PushManager', class {});
    Object.defineProperty(navigator, 'serviceWorker', {
      configurable: true,
      value: {
        getRegistration: async () => {
          throw new DOMException('no', 'SecurityError');
        },
      },
    });
    await expect(readPushStatus()).resolves.toBe('unsupported');
  });
});

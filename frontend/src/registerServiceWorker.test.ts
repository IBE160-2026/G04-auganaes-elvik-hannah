// Story 1.1 (AD-12): the service worker is registered at the root scope, in production only.
import { registerServiceWorker } from './registerServiceWorker';

const register = vi.fn().mockResolvedValue({});
// load listeners added by each test, removed afterwards so they cannot fire in the next one
const loadListeners: EventListenerOrEventListenerObject[] = [];
const addEventListener = window.addEventListener.bind(window);

beforeEach(() => {
  register.mockClear();
  vi.spyOn(window, 'addEventListener').mockImplementation((type, listener, options) => {
    if (type === 'load' && listener) loadListeners.push(listener);
    addEventListener(type, listener, options);
  });
  Object.defineProperty(window.navigator, 'serviceWorker', {
    value: { register },
    configurable: true,
  });
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  loadListeners.splice(0).forEach((listener) => window.removeEventListener('load', listener));
  delete (window.navigator as { serviceWorker?: unknown }).serviceWorker;
});

describe('registerServiceWorker', () => {
  it('registers /service-worker.js with scope "/" on load in production', () => {
    vi.stubEnv('PROD', true);
    registerServiceWorker();
    window.dispatchEvent(new Event('load'));

    expect(register).toHaveBeenCalledWith('/service-worker.js', { scope: '/' });
  });

  it('does not register outside production', () => {
    vi.stubEnv('PROD', false);
    registerServiceWorker();
    window.dispatchEvent(new Event('load'));

    expect(register).not.toHaveBeenCalled();
  });
});

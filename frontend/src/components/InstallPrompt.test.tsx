// Story 1.1 (AD-12): install prompt shown once per device, only on mobile and when not installed.
import { act, cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const IPHONE_UA =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';
const ANDROID_UA =
  'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36';
const IPADOS_UA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15';
const DESKTOP_UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36';

function setUserAgent(ua: string) {
  vi.spyOn(window.navigator, 'userAgent', 'get').mockReturnValue(ua);
}

function fireAppInstalled() {
  act(() => {
    window.dispatchEvent(new Event('appinstalled'));
  });
}

function setStandalone(standalone: boolean) {
  vi.mocked(window.matchMedia).mockImplementation((query: string) => ({
    matches: standalone && query === '(display-mode: standalone)',
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

// Fresh module per test so the in-memory "shown this session" flag starts empty.
async function renderPrompt() {
  const module = await import('./InstallPrompt');
  render(<module.InstallPrompt />);
  return module;
}

function fireBeforeInstallPrompt(prompt = vi.fn().mockResolvedValue(undefined)) {
  const event = Object.assign(new Event('beforeinstallprompt', { cancelable: true }), { prompt });
  act(() => {
    window.dispatchEvent(event);
  });
  return event;
}

const TITLE = 'Legg Husly på Hjem-skjermen';

beforeEach(() => {
  vi.resetModules();
  window.localStorage.clear();
  setStandalone(false);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('InstallPrompt', () => {
  it('shows iOS instructions on first visit and writes the flag when shown', async () => {
    setUserAgent(IPHONE_UA);
    const { INSTALL_PROMPT_FLAG } = await renderPrompt();

    expect(screen.getByRole('heading', { name: TITLE })).toBeInTheDocument();
    expect(screen.getByText(/Legg til på Hjem-skjerm/)).toBeInTheDocument();
    expect(window.localStorage.getItem(INSTALL_PROMPT_FLAG)).not.toBeNull();
  });

  it('is not shown when the flag is already set', async () => {
    setUserAgent(IPHONE_UA);
    window.localStorage.setItem('husly.installPromptShown', '2026-10-25T10:00:00.000Z');
    await renderPrompt();

    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
  });

  it('is not shown when the app already runs installed', async () => {
    setUserAgent(IPHONE_UA);
    setStandalone(true);
    await renderPrompt();

    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
  });

  it('is not shown on desktop, even if the browser offers install', async () => {
    setUserAgent(DESKTOP_UA);
    await renderPrompt();
    fireBeforeInstallPrompt();

    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
  });

  it('on Android waits for beforeinstallprompt and opens the native dialog', async () => {
    setUserAgent(ANDROID_UA);
    await renderPrompt();
    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();

    const event = fireBeforeInstallPrompt();
    expect(event.defaultPrevented).toBe(true);
    await userEvent.click(screen.getByRole('button', { name: 'Installer' }));

    expect(event.prompt).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
  });

  it('hides when dismissed', async () => {
    setUserAgent(IPHONE_UA);
    await renderPrompt();
    await userEvent.click(screen.getByRole('button', { name: 'Lukk' }));

    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
  });

  it('shows once this session and never crashes when localStorage throws', async () => {
    setUserAgent(IPHONE_UA);
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('SecurityError');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('SecurityError');
    });
    const { InstallPrompt } = await renderPrompt();
    expect(screen.getByRole('heading', { name: TITLE })).toBeInTheDocument();

    // A second mount in the same page load (same module) stays hidden.
    cleanup();
    render(<InstallPrompt />);
    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
  });

  it('treats iPadOS (desktop Safari UA with touch) as iOS', async () => {
    setUserAgent(IPADOS_UA);
    vi.spyOn(window.navigator, 'platform', 'get').mockReturnValue('MacIntel');
    // jsdom has no maxTouchPoints, so it is defined for this test only.
    Object.defineProperty(window.navigator, 'maxTouchPoints', { value: 5, configurable: true });
    try {
      await renderPrompt();
      expect(screen.getByRole('heading', { name: TITLE })).toBeInTheDocument();
      expect(screen.getByText(/Legg til på Hjem-skjerm/)).toBeInTheDocument();
    } finally {
      delete (window.navigator as { maxTouchPoints?: number }).maxTouchPoints;
    }
  });

  it('is not shown when iOS reports navigator.standalone', async () => {
    setUserAgent(IPHONE_UA);
    Object.defineProperty(window.navigator, 'standalone', { value: true, configurable: true });
    try {
      await renderPrompt();
      expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
    } finally {
      delete (window.navigator as Navigator & { standalone?: boolean }).standalone;
    }
  });

  it.each([
    ['Chrome', 'CriOS/140.0.0.0'],
    ['Firefox', 'FxiOS/140.0'],
    ['Edge', 'EdgiOS/140.0'],
    ['Facebook webview', '[FBAN/FBIOS;FBAV/500.0]'],
    ['Instagram webview', 'Instagram 400.0'],
    ['Line webview', 'Line/14.0'],
  ])('is not shown in %s on iOS and keeps the flag unused', async (_name, token) => {
    setUserAgent(`${IPHONE_UA} ${token}`);
    const { INSTALL_PROMPT_FLAG } = await renderPrompt();

    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
    expect(window.localStorage.getItem(INSTALL_PROMPT_FLAG)).toBeNull();
  });

  it('on Android hides when "Ikke nå" is tapped', async () => {
    setUserAgent(ANDROID_UA);
    await renderPrompt();
    const event = fireBeforeInstallPrompt();
    await userEvent.click(screen.getByRole('button', { name: 'Ikke nå' }));

    expect(event.prompt).not.toHaveBeenCalled();
    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
  });

  it('on Android without beforeinstallprompt shows nothing and writes no flag', async () => {
    setUserAgent(ANDROID_UA);
    const { INSTALL_PROMPT_FLAG } = await renderPrompt();

    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
    expect(window.localStorage.getItem(INSTALL_PROMPT_FLAG)).toBeNull();
  });

  it('on Android hides without an unhandled error when prompt() rejects', async () => {
    setUserAgent(ANDROID_UA);
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    await renderPrompt();
    const event = fireBeforeInstallPrompt(vi.fn().mockRejectedValue(new Error('InvalidStateError')));

    await userEvent.click(screen.getByRole('button', { name: 'Installer' }));

    expect(event.prompt).toHaveBeenCalledTimes(1);
    expect(consoleError).toHaveBeenCalled();
    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
  });

  it('on Android hides when the app gets installed another way', async () => {
    setUserAgent(ANDROID_UA);
    await renderPrompt();
    fireBeforeInstallPrompt();
    expect(screen.getByRole('heading', { name: TITLE })).toBeInTheDocument();

    fireAppInstalled();
    expect(screen.queryByRole('heading', { name: TITLE })).not.toBeInTheDocument();
  });
});

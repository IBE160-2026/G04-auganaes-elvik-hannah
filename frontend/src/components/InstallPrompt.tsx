import { useEffect, useState } from 'react';
import { PrimaryButton } from './PrimaryButton';
import './InstallPrompt.css';

/** localStorage key: the prompt is shown once per device (AD-12). */
export const INSTALL_PROMPT_FLAG = 'husly.installPromptShown';

/** Chrome's install event; not in the TypeScript DOM lib. */
type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
};

type Platform = 'ios' | 'android' | 'other';

// iOS browsers other than Safari, and in-app webviews, cannot use Safari's "Legg til på
// Hjem-skjerm" steps, so they get no prompt (and the once-per-device flag is not used up).
const IOS_NOT_SAFARI = /CriOS|FxiOS|EdgiOS|FBAN|FBAV|Instagram|Line\//i;

// Fallback when localStorage throws (private mode, blocked storage): show once per page load.
let shownThisSession = false;

function detectPlatform(): Platform {
  const ua = navigator.userAgent;
  const iPadOs = navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1;
  if (/iPhone|iPad|iPod/i.test(ua) || iPadOs) return IOS_NOT_SAFARI.test(ua) ? 'other' : 'ios';
  if (/Android/i.test(ua)) return 'android';
  return 'other';
}

function isStandalone(): boolean {
  const iosStandalone = (navigator as Navigator & { standalone?: boolean }).standalone === true;
  return iosStandalone || window.matchMedia('(display-mode: standalone)').matches;
}

function hasBeenShown(): boolean {
  if (shownThisSession) return true;
  try {
    return window.localStorage.getItem(INSTALL_PROMPT_FLAG) !== null;
  } catch {
    return false;
  }
}

function markShown(): void {
  shownThisSession = true;
  try {
    window.localStorage.setItem(INSTALL_PROMPT_FLAG, new Date().toISOString());
  } catch {
    // Storage unavailable: the in-memory flag above keeps it to once this session.
  }
}

/**
 * One shared "Add to Home Screen" prompt (Story 1.1, AD-12). Shown once per device on mobile,
 * never when the app already runs installed or on desktop. Android/Chrome uses the native
 * install dialog; iOS Safari has none, so it gets written instructions.
 */
export function InstallPrompt() {
  const [platform] = useState(detectPlatform);
  const [eligible] = useState(() => platform !== 'other' && !isStandalone() && !hasBeenShown());
  const [installEvent, setInstallEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!eligible || platform !== 'android') return;
    function onBeforeInstallPrompt(event: Event) {
      event.preventDefault();
      setInstallEvent(event as BeforeInstallPromptEvent);
    }
    function onAppInstalled() {
      setDismissed(true);
    }
    window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt);
    window.addEventListener('appinstalled', onAppInstalled);
    return () => {
      window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt);
      window.removeEventListener('appinstalled', onAppInstalled);
    };
  }, [eligible, platform]);

  // installEvent is only ever set on Android.
  const visible = eligible && !dismissed && (platform === 'ios' || installEvent !== null);

  useEffect(() => {
    if (visible) markShown();
  }, [visible]);

  if (!visible) return null;

  async function install() {
    if (!installEvent) return;
    // The event can only prompt once; clear it so a second tap cannot reuse it.
    const event = installEvent;
    setInstallEvent(null);
    try {
      await event.prompt();
    } catch (error: unknown) {
      console.error('Kunne ikke åpne installeringsdialogen', error);
    } finally {
      setDismissed(true);
    }
  }

  return (
    <section className="install-prompt" aria-labelledby="install-prompt-title">
      <h2 id="install-prompt-title" className="install-prompt__title">
        Legg Husly på Hjem-skjermen
      </h2>
      {platform === 'ios' ? (
        <p>
          Trykk på Del-knappen i Safari og velg «Legg til på Hjem-skjerm». Da åpnes Husly som en
          app, og du kan få varsler senere.
        </p>
      ) : (
        <p>Installer Husly som en app, så finner du oppgavene raskt og kan få varsler senere.</p>
      )}
      <div className="install-prompt__actions">
        {platform === 'android' && <PrimaryButton onClick={install}>Installer</PrimaryButton>}
        <button type="button" className="install-prompt__dismiss" onClick={() => setDismissed(true)}>
          {platform === 'ios' ? 'Lukk' : 'Ikke nå'}
        </button>
      </div>
    </section>
  );
}

// Story 2.2 (decision 9, UX-DR36), shared with the Portfolio in Story 6.1: pull-to-refresh for a
// page whose document scrolls. Only a pull that starts with the page scrolled to the top counts,
// and the browser's own pull-to-reload is turned off while the page is shown, so the app's pull is
// the only one. Restored on unmount. The visible «Oppdater» button stays the keyboard route.
import { useEffect, useRef, useState, type TouchEvent } from 'react';

// How far (in CSS pixels) a pull from the top must go before releasing refreshes.
export const PULL_THRESHOLD = 64;

export function usePullToRefresh(onRelease: () => void) {
  const [pulled, setPulled] = useState(false);
  const pullStart = useRef<number | null>(null);

  useEffect(() => {
    const root = document.documentElement;
    const previous = root.style.overscrollBehaviorY;
    root.style.overscrollBehaviorY = 'contain';
    return () => {
      root.style.overscrollBehaviorY = previous;
    };
  }, []);

  function cancel() {
    pullStart.current = null;
    setPulled(false);
  }

  const handlers = {
    onTouchStart(event: TouchEvent) {
      const atTop = (document.scrollingElement?.scrollTop ?? 0) <= 0;
      pullStart.current = atTop ? event.touches[0].clientY : null;
    },
    onTouchMove(event: TouchEvent) {
      if (pullStart.current === null) return;
      setPulled(event.touches[0].clientY - pullStart.current >= PULL_THRESHOLD);
    },
    onTouchEnd() {
      const release = pulled;
      cancel();
      if (release) onRelease();
    },
    onTouchCancel: cancel,
  };

  return { pulled, handlers };
}

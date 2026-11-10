// Story 2.2 (decision 14): after navigation, focus goes to the new page's heading, so a screen
// reader announces where the user landed and Tab continues from the top of the page. The
// heading needs tabIndex={-1}.
import { useEffect, useRef } from 'react';

export function useFocusOnMount<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);
  return ref;
}

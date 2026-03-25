'use client';

import { useEffect, useState } from 'react';

/** Tailwind `md` breakpoint (pixels). Viewports at or below this are treated as mobile. */
const MOBILE_MAX_WIDTH_PX = 767;

/**
 * `undefined` until mounted — use to avoid hydration mismatch and to defer desktop-only gating.
 */
export function useIsMobile(): boolean | undefined {
  const [isMobile, setIsMobile] = useState<boolean | undefined>(undefined);

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_MAX_WIDTH_PX}px)`);
    const apply = () => setIsMobile(mq.matches);
    apply();
    mq.addEventListener('change', apply);
    return () => mq.removeEventListener('change', apply);
  }, []);

  return isMobile;
}

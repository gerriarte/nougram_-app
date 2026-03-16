'use client';

import { usePathname, useSearchParams } from 'next/navigation';
import { useEffect, useRef } from 'react';
import { trackPageView } from '@/lib/analytics';

export function RouteTracker(): null {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const prevPathRef = useRef<string | null>(null);

  useEffect(() => {
    const path = pathname ?? '/';
    const search = searchParams?.toString() ?? '';
    const key = `${path}?${search}`;
    if (prevPathRef.current === key) return;
    prevPathRef.current = key;
    trackPageView({ path, search });
  }, [pathname, searchParams]);

  return null;
}

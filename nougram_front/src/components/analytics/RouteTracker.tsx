'use client';

import { usePathname, useSearchParams } from 'next/navigation';
import React, { Suspense, useEffect, useRef, useState } from 'react';
import { trackPageView } from '@/lib/analytics';

function RouteTrackerInner(): null {
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

export function RouteTracker(): React.ReactNode {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) return null;
  return (
    <Suspense fallback={null}>
      <RouteTrackerInner />
    </Suspense>
  );
}

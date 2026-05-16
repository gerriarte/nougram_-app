'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';

const RouteTracker = dynamic(
  () => import('@/components/analytics/RouteTracker').then((m) => m.RouteTracker),
  { ssr: false }
);

export function RouteTrackerClient() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) return null;
  return <RouteTracker />;
}

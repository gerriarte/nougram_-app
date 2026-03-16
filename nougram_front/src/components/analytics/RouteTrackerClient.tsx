'use client';

import dynamic from 'next/dynamic';

const RouteTracker = dynamic(
  () => import('@/components/analytics/RouteTracker').then((m) => m.RouteTracker),
  { ssr: false }
);

export function RouteTrackerClient() {
  return <RouteTracker />;
}

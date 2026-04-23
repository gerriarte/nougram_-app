import React from 'react';

// Dashboard is authenticated, user-specific, and data-driven.
// Force dynamic rendering to avoid unnecessary static prerender work at build time.
export const dynamic = 'force-dynamic';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    return children;
}


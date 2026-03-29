'use client';

import React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { removeAuthToken } from '@/lib/auth';

type AuthExpiredDetail = {
  reason?: string;
  statusCode?: number;
  endpoint?: string;
};

export function AuthSessionExpiredDialog() {
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const onAuthExpired = (event: Event) => {
      const customEvent = event as CustomEvent<AuthExpiredDetail>;
      const reason = customEvent.detail?.reason;
      // Show modal only for backend 401 flows, not explicit logout actions.
      if (reason && reason !== 'unauthorized') return;
      if (pathname?.startsWith('/login')) return;
      setOpen(true);
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('nougram:auth-expired', onAuthExpired as EventListener);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('nougram:auth-expired', onAuthExpired as EventListener);
      }
    };
  }, [pathname]);

  const goToLogin = React.useCallback(() => {
    removeAuthToken();
    const redirect = encodeURIComponent(pathname || '/dashboard');
    setOpen(false);
    router.replace(`/login?redirect=${redirect}`);
  }, [pathname, router]);

  if (pathname?.startsWith('/login')) return null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-[460px]">
        <DialogHeader>
          <DialogTitle>Sesion expirada</DialogTitle>
          <DialogDescription>
            Tu sesion ya no es valida. Para continuar, inicia sesion nuevamente.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="primary" onClick={goToLogin}>
            Ir a iniciar sesion
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

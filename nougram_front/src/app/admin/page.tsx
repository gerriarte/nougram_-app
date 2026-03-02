"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminPage() {
    const router = useRouter();

    useEffect(() => {
        // Legacy /admin route used local mock calculations.
        // Redirect to backend-driven admin payroll module.
        router.replace("/admin/payroll");
    }, [router]);

    return null;
}

"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function RouteGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // If auth state has resolved and no user session exists, redirect to login
    if (!isLoading && !user && pathname !== "/login") {
      router.push("/login");
    }
  }, [user, isLoading, pathname, router]);

  return <>{children}</>;
}

"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { usePathname, useRouter } from "next/navigation";

import type { AuthUser } from "@/lib/auth";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  setUser: (user: AuthUser) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    function handleUnauthorized() {
      const returnTo = `${window.location.pathname}${window.location.search}`;
      setUser(null);
      router.replace(`/login?returnTo=${encodeURIComponent(returnTo)}`);
    }

    window.addEventListener("cybersentinel:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener(
        "cybersentinel:unauthorized",
        handleUnauthorized,
      );
    };
  }, [router]);

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      try {
        const response = await fetch("/api/auth/me", {
          cache: "no-store",
        });

        if (!response.ok) {
          if (!cancelled && pathname !== "/login") {
            const returnTo = `${window.location.pathname}${window.location.search}`;
            router.replace(`/login?returnTo=${encodeURIComponent(returnTo)}`);
          }
          return;
        }

        const currentUser = (await response.json()) as AuthUser;
        if (!cancelled) {
          setUser(currentUser);
          if (pathname === "/login") {
            router.replace("/");
          }
        }
      } catch {
        if (!cancelled && pathname !== "/login") {
          const returnTo = `${window.location.pathname}${window.location.search}`;
          router.replace(`/login?returnTo=${encodeURIComponent(returnTo)}`);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadUser();

    return () => {
      cancelled = true;
    };
  }, [pathname, router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      setUser,
      logout: async () => {
        await fetch("/api/auth/logout", { method: "POST" });
        setUser(null);
        router.replace("/login");
        router.refresh();
      },
    }),
    [isLoading, router, user],
  );

  if (pathname !== "/login" && (isLoading || !user)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <div className="text-center">
          <div className="mx-auto size-9 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
          <p className="mt-4 text-sm text-slate-300">
            Verifying secure session...
          </p>
        </div>
      </div>
    );
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}

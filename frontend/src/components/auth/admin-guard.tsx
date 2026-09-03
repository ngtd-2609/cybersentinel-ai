"use client";

import Link from "next/link";
import { ShieldX } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Button } from "@/components/ui/button";

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  if (user?.role !== "ADMIN") {
    return (
      <main className="flex min-h-[70vh] items-center justify-center p-6">
        <div className="max-w-md text-center">
          <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-red-50 ring-1 ring-red-200">
            <ShieldX className="size-7 text-red-600" />
          </div>
          <h1 className="mt-5 text-2xl font-semibold text-slate-950">
            Administrator access required
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            Your current role cannot view or modify administration data.
          </p>
          <Button render={<Link href="/" />} className="mt-6">
            Return to dashboard
          </Button>
        </div>
      </main>
    );
  }

  return children;
}

"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { LockKeyhole, ShieldCheck } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { AuthUser } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch(
        mfaToken ? "/api/auth/mfa/verify" : "/api/auth/login",
        {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          mfaToken
            ? { mfa_token: mfaToken, code: mfaCode }
            : { email, password },
        ),
      },
      );

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "Unable to sign in");
      }

      if (response.status === 202) {
        const challenge = (await response.json()) as { mfa_token: string };
        setMfaToken(challenge.mfa_token);
        setPassword("");
        return;
      }

      const user = (await response.json()) as AuthUser;
      setUser(user);

      const requestedPath = new URLSearchParams(
        window.location.search,
      ).get("returnTo");
      const returnTo =
        requestedPath?.startsWith("/") && !requestedPath.startsWith("//")
          ? requestedPath
          : "/";
      router.replace(returnTo);
      router.refresh();
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Unable to sign in",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 px-5 py-12 text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(6,182,212,0.16),transparent_36%),radial-gradient(circle_at_bottom_right,rgba(14,116,144,0.12),transparent_32%)]" />
      <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(rgba(148,163,184,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.12)_1px,transparent_1px)] [background-size:42px_42px]" />

      <div className="relative grid w-full max-w-5xl items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="hidden lg:block">
          <div className="mb-8 flex size-14 items-center justify-center rounded-2xl border border-cyan-400/30 bg-cyan-400/10">
            <ShieldCheck className="size-8 text-cyan-300" />
          </div>
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-cyan-300">
            CyberSentinel AI
          </p>
          <h1 className="mt-4 max-w-xl text-5xl font-semibold leading-tight tracking-tight">
            Secure access to your SOC command center.
          </h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-slate-300">
            Authenticate to investigate detections, coordinate incident response,
            and use AI-assisted security analysis.
          </p>
          <div className="mt-9 flex items-center gap-3 text-sm text-emerald-300">
            <span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_18px_rgba(52,211,153,0.8)]" />
            Security services operational
          </div>
        </section>

        <Card className="border-white/10 bg-white text-slate-950 shadow-2xl shadow-cyan-950/30">
          <CardHeader className="space-y-3 px-7 pt-8 sm:px-9">
            <div className="flex size-11 items-center justify-center rounded-xl bg-cyan-50 ring-1 ring-cyan-200 lg:hidden">
              <ShieldCheck className="size-6 text-cyan-700" />
            </div>
            <CardTitle className="text-2xl">
              {mfaToken ? "Verify administrator access" : "Sign in to CyberSentinel"}
            </CardTitle>
            <CardDescription>
              {mfaToken
                ? "Enter a current authenticator code or a one-time recovery code."
                : "Use your authorized SOC account to continue."}
            </CardDescription>
          </CardHeader>

          <CardContent className="px-7 pb-8 sm:px-9">
            <form className="space-y-5" onSubmit={handleSubmit}>
              {!mfaToken ? <><div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email address
                </label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="analyst@company.com"
                  required
                  autoFocus
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter your password"
                  required
                />
              </div></> : <div className="space-y-2">
                <label htmlFor="mfa-code" className="text-sm font-medium">
                  Authenticator or recovery code
                </label>
                <Input
                  id="mfa-code"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  value={mfaCode}
                  onChange={(event) => setMfaCode(event.target.value)}
                  placeholder="000000"
                  required
                  autoFocus
                />
              </div>}

              {error && (
                <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                disabled={isSubmitting}
                className="h-11 w-full bg-slate-950 text-white hover:bg-slate-800"
              >
                <LockKeyhole className="size-4" />
                {isSubmitting
                  ? "Verifying..."
                  : mfaToken
                    ? "Verify MFA"
                    : "Sign in securely"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

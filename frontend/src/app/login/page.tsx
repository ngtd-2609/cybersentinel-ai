"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { LoaderCircle, LockKeyhole, ShieldCheck, Sparkles, UserPlus } from "lucide-react";

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
  const demoLoginEnabled =
    process.env.NEXT_PUBLIC_DEMO_LOGIN_ENABLED === "true";
  const registrationEnabled =
    process.env.NEXT_PUBLIC_REGISTRATION_ENABLED === "true";
  const router = useRouter();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serviceStatus, setServiceStatus] = useState<
    "checking" | "ready" | "waking"
  >("checking");

  useEffect(() => {
    if (!demoLoginEnabled) {
      return;
    }
    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    async function checkService() {
      try {
        const response = await fetch("/api/health", { cache: "no-store" });
        if (cancelled) {
          return;
        }
        if (response.ok) {
          setServiceStatus("ready");
          return;
        }
      } catch {
        // A sleeping free-tier backend is expected to fail initial checks.
      }
      if (!cancelled) {
        setServiceStatus("waking");
        retryTimer = setTimeout(checkService, 3000);
      }
    }

    void checkService();
    return () => {
      cancelled = true;
      if (retryTimer) {
        clearTimeout(retryTimer);
      }
    };
  }, [demoLoginEnabled]);

  function finishLogin(user: AuthUser) {
    setUser(user);
    const requestedPath = new URLSearchParams(window.location.search).get(
      "returnTo",
    );
    const returnTo =
      requestedPath?.startsWith("/") && !requestedPath.startsWith("//")
        ? requestedPath
        : "/";
    router.replace(returnTo);
    router.refresh();
  }

  async function handleDemoLogin() {
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await fetch("/api/auth/demo", { method: "POST" });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "Unable to start the portfolio demo");
      }
      finishLogin((await response.json()) as AuthUser);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Unable to start the portfolio demo",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (authMode === "register" && password !== confirmPassword) {
        throw new Error("Passwords do not match");
      }
      const response = await fetch(
        authMode === "register"
          ? "/api/auth/register"
          : mfaToken
            ? "/api/auth/mfa/verify"
            : "/api/auth/login",
        {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          authMode === "register"
            ? { email, username, full_name: fullName.trim() || null, password }
            : mfaToken
            ? { mfa_token: mfaToken, code: mfaCode }
            : { email, password },
        ),
      },
      );

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail;
        const message = Array.isArray(detail)
          ? detail.map((item) => item?.msg).filter(Boolean).join(". ")
          : detail;
        throw new Error(message || (authMode === "register" ? "Unable to create account" : "Unable to sign in"));
      }

      if (response.status === 202) {
        const challenge = (await response.json()) as { mfa_token: string };
        setMfaToken(challenge.mfa_token);
        setPassword("");
        return;
      }

      const user = (await response.json()) as AuthUser | { detail?: string };
      if (!("id" in user)) {
        setAuthMode("login");
        throw new Error(user.detail ?? "Account created. Please sign in.");
      }
      finishLogin(user);
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
              {mfaToken
                ? "Verify administrator access"
                : authMode === "register"
                  ? "Create your CyberSentinel account"
                  : "Sign in to CyberSentinel"}
            </CardTitle>
            <CardDescription>
              {mfaToken
                ? "Enter a current authenticator code or a one-time recovery code."
                : authMode === "register"
                  ? "Create a viewer account with a private threat-simulation sandbox."
                  : "Use your authorized SOC account to continue."}
            </CardDescription>
            {demoLoginEnabled && !mfaToken && authMode === "login" && (
              <div
                aria-live="polite"
                className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs ${
                  serviceStatus === "ready"
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border-amber-200 bg-amber-50 text-amber-800"
                }`}
              >
                {serviceStatus === "ready" ? (
                  <span className="size-2 rounded-full bg-emerald-500" />
                ) : (
                  <LoaderCircle className="size-3.5 animate-spin" />
                )}
                {serviceStatus === "ready"
                  ? "Portfolio demo services are ready."
                  : "Waking free-tier demo services. This can take about a minute."}
              </div>
            )}
          </CardHeader>

          <CardContent className="px-7 pb-8 sm:px-9">
            <form className="space-y-5" onSubmit={handleSubmit}>
              {!mfaToken ? <>
              {authMode === "register" && <><div className="space-y-2">
                <label htmlFor="full-name" className="text-sm font-medium">Full name <span className="text-slate-400">(optional)</span></label>
                <Input id="full-name" autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Your name" maxLength={255} />
              </div>
              <div className="space-y-2">
                <label htmlFor="username" className="text-sm font-medium">Username</label>
                <Input id="username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} placeholder="security-viewer" minLength={3} maxLength={64} pattern="[A-Za-z0-9_.-]+" required />
              </div></>}
              <div className="space-y-2">
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
                  autoComplete={authMode === "register" ? "new-password" : "current-password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={authMode === "register" ? "At least 12 characters" : "Enter your password"}
                  minLength={authMode === "register" ? 12 : undefined}
                  required
                />
                {authMode === "register" && <p className="text-xs leading-5 text-slate-500">Use at least 12 characters with uppercase, lowercase, number and special character.</p>}
              </div>
              {authMode === "register" && <div className="space-y-2">
                <label htmlFor="confirm-password" className="text-sm font-medium">Confirm password</label>
                <Input id="confirm-password" type="password" autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Repeat your password" minLength={12} required />
              </div>}</> : <div className="space-y-2">
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
                {authMode === "register" ? <UserPlus className="size-4" /> : <LockKeyhole className="size-4" />}
                {isSubmitting
                  ? authMode === "register" ? "Creating account..." : "Verifying..."
                  : mfaToken
                    ? "Verify MFA"
                    : authMode === "register"
                      ? "Create account"
                      : "Sign in securely"}
              </Button>
            </form>
            {registrationEnabled && !mfaToken && (
              <div className="mt-4 text-center text-sm text-slate-600">
                {authMode === "register" ? "Already have an account?" : "New to CyberSentinel?"}{" "}
                <button
                  type="button"
                  className="font-semibold text-cyan-700 hover:underline"
                  onClick={() => {
                    setAuthMode((mode) => mode === "login" ? "register" : "login");
                    setError(null);
                  }}
                >
                  {authMode === "register" ? "Sign in" : "Create account"}
                </button>
              </div>
            )}
            {demoLoginEnabled && !mfaToken && authMode === "login" && (
              <div className="mt-5 space-y-4 border-t pt-5">
                <Button
                  type="button"
                  variant="outline"
                  disabled={isSubmitting || serviceStatus !== "ready"}
                  className="h-11 w-full"
                  onClick={handleDemoLogin}
                >
                  <Sparkles className="size-4" />
                  Explore with the safe demo account
                </Button>
                <p className="text-center text-xs leading-5 text-slate-500">
                  Uses synthetic security data. Demo records stay read-only, while your private sandbox remains interactive.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

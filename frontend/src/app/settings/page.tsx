"use client";

import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Globe2, KeyRound, LockKeyhole, Settings2, UserRound } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatRole } from "@/lib/auth";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api/client";

async function changePassword(payload: { current_password: string; new_password: string }) {
  const response = await apiFetch("/auth/change-password", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "Unable to change password");
  }
}

export default function SettingsPage() {
  const { user } = useAuth();
  const { locale, setLocale, t } = useLanguage();
  const [passwords, setPasswords] = useState({ current_password: "", new_password: "", confirm: "" });
  const [passwordChanged, setPasswordChanged] = useState(false);
  const passwordMutation = useMutation({ mutationFn: changePassword, onSuccess: () => { setPasswords({ current_password: "", new_password: "", confirm: "" }); setPasswordChanged(true); } });
  function submitPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordChanged(false);
    if (passwords.new_password !== passwords.confirm) return;
    passwordMutation.mutate({ current_password: passwords.current_password, new_password: passwords.new_password });
  }

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-5xl p-5 md:p-8">
          <header className="mb-8">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">
              <Settings2 className="size-4" /> {t("Settings")}
            </div>
            <h1 className="text-3xl font-semibold">{t("Language & experience")}</h1>
            <p className="mt-2 text-sm text-slate-500">{t("Choose the interface language used on this device.")}</p>
          </header>

          <section className="grid gap-5 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Globe2 className="size-5 text-cyan-600" />{t("Language & experience")}</CardTitle></CardHeader>
              <CardContent className="grid grid-cols-2 gap-3">
                <Button variant={locale === "en" ? "default" : "outline"} onClick={() => setLocale("en")}>{t("English")}</Button>
                <Button variant={locale === "vi" ? "default" : "outline"} onClick={() => setLocale("vi")}>{t("Vietnamese")}</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><UserRound className="size-5 text-violet-600" />{t("Account & security")}</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div><span className="text-slate-500">Email</span><p className="font-medium">{user?.email}</p></div>
                <div><span className="text-slate-500">Username</span><p className="font-medium">{user?.username}</p></div>
                <div className="flex items-center gap-2"><LockKeyhole className="size-4 text-slate-400" /><Badge variant="outline">{user ? formatRole(user.role) : "—"}</Badge></div>
                {user?.role === "VIEWER" && <p className="rounded-lg bg-cyan-50 p-3 text-cyan-800">{t("Demo records are read-only. Your threat simulations run in a private, temporary sandbox.")}</p>}
              </CardContent>
            </Card>

            <Card className="md:col-span-2"><CardHeader><CardTitle className="flex items-center gap-2"><KeyRound className="size-5 text-emerald-600" />{t("Change password")}</CardTitle></CardHeader><CardContent><form onSubmit={submitPassword} className="grid gap-4 md:grid-cols-3"><label className="grid gap-1 text-xs font-medium">{t("Current password")}<Input type="password" autoComplete="current-password" required value={passwords.current_password} onChange={(event) => setPasswords((value) => ({ ...value, current_password: event.target.value }))} /></label><label className="grid gap-1 text-xs font-medium">{t("New password")}<Input type="password" autoComplete="new-password" required minLength={12} value={passwords.new_password} onChange={(event) => setPasswords((value) => ({ ...value, new_password: event.target.value }))} /></label><label className="grid gap-1 text-xs font-medium">{t("Confirm new password")}<Input type="password" autoComplete="new-password" required minLength={12} value={passwords.confirm} onChange={(event) => setPasswords((value) => ({ ...value, confirm: event.target.value }))} /></label><div className="flex items-center gap-3 md:col-span-3"><Button type="submit" disabled={passwordMutation.isPending || passwords.new_password !== passwords.confirm}>{passwordMutation.isPending ? t("Updating...") : t("Update password")}</Button>{passwords.confirm && passwords.new_password !== passwords.confirm && <span className="text-sm text-red-600">{t("Passwords do not match.")}</span>}{passwordMutation.error && <span className="text-sm text-red-600">{passwordMutation.error.message}</span>}{passwordChanged && <span className="text-sm text-emerald-700">{t("Password updated successfully.")}</span>}</div></form><p className="mt-3 text-xs text-slate-500">{t("Use 12+ characters with uppercase, lowercase, a number and a symbol.")}</p></CardContent></Card>
          </section>
        </main>
      </div>
    </div>
  );
}

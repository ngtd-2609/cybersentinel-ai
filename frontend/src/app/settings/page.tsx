"use client";

import { Globe2, LockKeyhole, Settings2, UserRound } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatRole } from "@/lib/auth";

export default function SettingsPage() {
  const { user } = useAuth();
  const { locale, setLocale, t } = useLanguage();

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
                {user?.role === "VIEWER" && <p className="rounded-lg bg-cyan-50 p-3 text-cyan-800">{t("Your public account is read-only to keep the shared demo safe.")}</p>}
              </CardContent>
            </Card>
          </section>
        </main>
      </div>
    </div>
  );
}

"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Bell, Languages, LogOut, Menu, Search } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatRole } from "@/lib/auth";
import { Sidebar } from "@/components/dashboard/sidebar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";

export function Topbar() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const { locale, t, toggleLocale } = useLanguage();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const summary = useDashboardSummary();
  const alertCount = summary.data?.requires_review ?? 0;
  const initials = (user?.full_name ?? user?.username ?? "SOC Analyst")
    .split(/\s+/)
    .map((part) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = search.trim();
    if (!query) return;
    const eventMatch = query.match(/^(?:EVT-)?0*(\d+)$/i);
    router.push(eventMatch ? `/events/${eventMatch[1]}` : `/events?search=${encodeURIComponent(query)}`);
  }

  return (
    <header className="sticky top-0 z-30 flex h-20 items-center gap-4 border-b border-slate-200 bg-white/95 px-5 backdrop-blur md:px-8">
      <Button
        variant="ghost"
        size="icon"
        className="text-slate-500 lg:hidden"
        onClick={() => setMobileOpen(true)}
        aria-label={t("Navigation")}
        aria-expanded={mobileOpen}
      >
        <Menu className="size-5" />
      </Button>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-[19rem] p-0" showCloseButton>
          <SheetTitle className="sr-only">{t("Navigation")}</SheetTitle>
          <Sidebar mobile onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <form className="relative hidden w-full max-w-md md:block" onSubmit={submitSearch} role="search">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder="Search event, IP, CVE, IOC..."
          aria-label={t("Search security data")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="border-slate-200 bg-slate-50 pl-10 text-slate-900 placeholder:text-slate-400"
        />
      </form>

      <div className="ml-auto flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="hidden gap-2 text-slate-600 sm:flex"
          onClick={toggleLocale}
          aria-label={locale === "en" ? "Switch to Vietnamese" : "Chuyển sang tiếng Anh"}
        >
          <Languages className="size-4" />
          {locale.toUpperCase()}
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="relative text-slate-500"
          onClick={() => setNotificationsOpen((current) => !current)}
          aria-label={t("Notifications")}
          aria-expanded={notificationsOpen}
        >
          <Bell className="size-5" />
          {alertCount > 0 && <span className="absolute right-2 top-2 size-2 rounded-full bg-red-500" />}
        </Button>
        {notificationsOpen && (
          <div className="absolute right-16 top-16 z-50 w-80 rounded-xl border border-slate-200 bg-white p-4 shadow-xl" role="status">
            <p className="font-medium text-slate-900">{alertCount > 0 ? `${alertCount} ${t("events require review")}` : t("No new notifications")}</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">{alertCount > 0 ? t("Open Detection Events to investigate the current alerts.") : t("Your alerts and system updates will appear here.")}</p>
            {alertCount > 0 && <Button size="sm" className="mt-3" onClick={() => { setNotificationsOpen(false); router.push("/events"); }}>{t("Review alerts")}</Button>}
          </div>
        )}

        <div className="mx-1 h-8 w-px bg-slate-200" />

        <div className="flex items-center gap-3">
          <Avatar className="size-9 border border-cyan-100">
            <AvatarFallback className="bg-cyan-50 text-xs font-semibold text-cyan-700">
              {initials}
            </AvatarFallback>
          </Avatar>

          <div className="hidden sm:block">
            <p className="text-sm font-medium text-slate-900">
              {user?.full_name ?? user?.username ?? "SOC Analyst"}
            </p>
            <p className="text-xs text-slate-500">
              {user ? formatRole(user.role) : "Loading role"}
            </p>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => void logout()}
            className="text-slate-500 hover:text-red-600"
            aria-label={t("Sign out")}
            title={t("Sign out")}
          >
            <LogOut className="size-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}

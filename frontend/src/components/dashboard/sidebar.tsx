"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Bot,
  BrainCircuit,
  FileText,
  LayoutDashboard,
  Radar,
  ScrollText,
  Settings,
  ShieldCheck,
  Siren,
  Users,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { useLanguage } from "@/components/i18n/language-provider";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api/soc";

const operations = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Detection Events", href: "/events", icon: Siren },
  { label: "Incidents", href: "/incidents", icon: ShieldCheck },
  { label: "SOC Copilot", href: "/copilot", icon: Bot },
  { label: "Threat Intelligence", href: "/threat-intel", icon: Radar },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Model Monitor", href: "/models", icon: BrainCircuit },
  { label: "System Monitoring", href: "/monitoring", icon: Activity },
  { label: "Reports", href: "/reports", icon: FileText },
];

const administration = [
  { label: "Users & Roles", href: "/admin/users", icon: Users, adminOnly: true },
  { label: "Audit Logs", href: "/admin/audit-logs", icon: ScrollText, adminOnly: true },
  { label: "Settings", href: "/settings", icon: Settings, adminOnly: false },
];

export function Sidebar({ mobile = false, onNavigate }: { mobile?: boolean; onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user } = useAuth();
  const { t } = useLanguage();
  const health = useQuery({ queryKey: ["api-health"], queryFn: getHealth, refetchInterval: 60_000, retry: 1 });
  const healthy = health.data?.status === "ok";
  const administrationItems = administration.filter(
    (item) => !item.adminOnly || user?.role === "ADMIN",
  );

  return (
    <aside className={cn("h-screen w-72 shrink-0 border-r border-slate-200 bg-white flex-col", mobile ? "flex w-full" : "hidden lg:flex")}>
      <div className="flex h-20 items-center gap-3 border-b border-slate-200 px-6">
        <div className="flex size-10 items-center justify-center rounded-xl bg-cyan-50 ring-1 ring-cyan-200">
          <ShieldCheck className="size-6 text-cyan-600" />
        </div>

        <div>
          <p className="font-semibold tracking-tight text-slate-950">
            CyberSentinel AI
          </p>
          <p className="text-xs text-slate-500">Security Operations</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <p className="mb-3 px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
          {t("Operations")}
        </p>

        <nav className="space-y-1">
          {operations.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onNavigate}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                  active
                    ? "bg-cyan-50 text-cyan-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                )}
              >
                <item.icon
                  className={cn(
                    "size-4",
                    active ? "text-cyan-600" : "text-slate-400",
                  )}
                />
                {t(item.label)}
              </Link>
            );
          })}
        </nav>

        <p className="mb-3 mt-8 px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
          {t("Administration")}
        </p>

        <nav className="space-y-1">
          {administrationItems.map((item) => {
            const active = pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onNavigate}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                  active
                    ? "bg-cyan-50 text-cyan-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                )}
              >
                <item.icon
                  className={cn(
                    "size-4",
                    active ? "text-cyan-600" : "text-slate-400",
                  )}
                />
                {t(item.label)}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="border-t border-slate-200 p-4">
        <div className={`rounded-xl border p-4 ${healthy ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"}`}>
          <div className={`flex items-center gap-2 text-sm font-medium ${healthy ? "text-emerald-700" : "text-amber-700"}`}>
            <span className={`size-2 rounded-full ${healthy ? "bg-emerald-500" : "bg-amber-500"}`} />
            {healthy ? t("System Operational") : t("Checking system")}
          </div>
          <p className={`mt-1 text-xs ${healthy ? "text-emerald-700/70" : "text-amber-700/70"}`}>
            {healthy ? t("Detection services online") : t("Waiting for API health check")}
          </p>
        </div>
      </div>
    </aside>
  );
}

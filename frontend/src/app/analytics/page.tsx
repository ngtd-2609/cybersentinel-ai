"use client";

import { Activity, BarChart3, Crosshair, ShieldAlert } from "lucide-react";

import { AttackTypesChart } from "@/components/dashboard/attack-types-chart";
import { SecurityEventsChart } from "@/components/dashboard/security-events-chart";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";

export default function AnalyticsPage() {
  const { data, isLoading, isError } = useDashboardSummary();
  const metrics = data ? [
    { label: "Event volume", value: data.total_events, icon: Activity },
    { label: "Critical ratio", value: data.total_events ? `${((data.critical_alerts / data.total_events) * 100).toFixed(1)}%` : "0%", icon: ShieldAlert },
    { label: "Average risk", value: data.average_risk_score.toFixed(1), icon: Crosshair },
    { label: "Review queue", value: data.requires_review, icon: BarChart3 },
  ] : [];

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-[1600px] p-5 md:p-8">
          <header className="mb-8"><p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">Detection intelligence</p><h1 className="text-3xl font-semibold tracking-tight">Security Analytics</h1><p className="mt-2 text-sm text-slate-500">Live severity, risk and attack-pattern analysis from stored detection events.</p></header>
          {isError ? <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">Unable to load analytics.</p> : (
            <>
              <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {isLoading ? Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} className="h-28 rounded-xl" />) : metrics.map((metric) => (
                  <Card key={metric.label}><CardContent className="flex items-center justify-between p-5"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{metric.label}</p><p className="mt-2 text-3xl font-semibold">{metric.value}</p></div><metric.icon className="size-7 text-cyan-600" /></CardContent></Card>
                ))}
              </section>
              <section className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(340px,1fr)]">
                <Card><CardHeader><CardTitle>24-hour event trend</CardTitle></CardHeader><CardContent><SecurityEventsChart /></CardContent></Card>
                <Card><CardHeader><CardTitle>Attack distribution</CardTitle></CardHeader><CardContent><AttackTypesChart /></CardContent></Card>
              </section>
              <Card className="mt-6"><CardHeader><CardTitle>Top threat sources</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {data?.top_threat_sources.length ? data.top_threat_sources.map((source) => (
                  <article key={source.source_ip} className="flex items-center justify-between rounded-xl border bg-slate-50 p-4"><div><p className="font-mono text-sm font-semibold">{source.source_ip}</p><p className="mt-1 text-xs text-slate-500">{source.count} detection{source.count === 1 ? "" : "s"}</p></div><Badge variant="outline" className="border-red-200 bg-red-50 text-red-700">Risk {source.max_risk_score.toFixed(0)}</Badge></article>
                )) : <p className="text-sm text-slate-500">No source intelligence available.</p>}
              </CardContent></Card>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

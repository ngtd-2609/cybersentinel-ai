"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, Clock3, Cpu, Database, Gauge, RefreshCw } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLanguage } from "@/components/i18n/language-provider";
import { getComponentStatus, getHealth, getPrometheusMetrics, metricSum, metricValue } from "@/lib/api/soc";

function bytes(value: number | null): string {
  return value === null ? "—" : `${(value / 1024 / 1024).toFixed(1)} MB`;
}

export default function MonitoringPage() {
  const { t } = useLanguage();
  const health = useQuery({ queryKey: ["api-health"], queryFn: getHealth, refetchInterval: 15_000 });
  const metrics = useQuery({ queryKey: ["prometheus-metrics"], queryFn: getPrometheusMetrics, refetchInterval: 15_000 });
  const components = useQuery({ queryKey: ["component-status"], queryFn: getComponentStatus, refetchInterval: 30_000 });
  const text = metrics.data ?? "";
  const startedAt = metricValue(text, "process_start_time_seconds");
  const cards = [
    { label: "Resident memory", value: bytes(metricValue(text, "process_resident_memory_bytes")), icon: Database },
    { label: "CPU time", value: `${metricValue(text, "process_cpu_seconds_total")?.toFixed(1) ?? "—"}s`, icon: Cpu },
    { label: "HTTP requests", value: metricSum(text, "cybersentinel_http_requests_total").toLocaleString(), icon: Gauge },
    { label: "Process uptime", value: startedAt && metrics.dataUpdatedAt ? `${Math.floor(metrics.dataUpdatedAt / 1000 - startedAt)}s` : "—", icon: Clock3 },
  ];
  const refreshing = health.isFetching || metrics.isFetching || components.isFetching;

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-[1500px] p-5 md:p-8">
          <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700"><Activity className="size-4" />{t("Runtime telemetry")}</div><h1 className="text-3xl font-semibold tracking-tight">{t("System Monitoring")}</h1><p className="mt-2 text-sm text-slate-500">{t("Live API health and Prometheus process metrics, refreshed every 15 seconds.")}</p></div><Button variant="outline" disabled={refreshing} onClick={() => { health.refetch(); metrics.refetch(); components.refetch(); }}><RefreshCw className={refreshing ? "animate-spin" : ""} />{t("Refresh")}</Button></header>
          <Card className={health.isSuccess ? "mb-6 border-emerald-200 bg-emerald-50" : "mb-6 border-amber-200 bg-amber-50"}><CardContent className="flex items-center justify-between p-5"><div><p className="font-semibold">CyberSentinel API</p><p className="mt-1 text-sm text-slate-600">{health.isSuccess ? t("Health endpoint is responding normally.") : health.isLoading ? t("Checking service health...") : t("Health check failed.")}</p></div><Badge className={health.isSuccess ? "bg-emerald-600" : "bg-amber-600"}>{health.isSuccess ? health.data.status.toUpperCase() : t("UNAVAILABLE")}</Badge></CardContent></Card>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map((card) => <Card key={card.label}><CardContent className="flex items-center justify-between p-5"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t(card.label)}</p><p className="mt-2 text-2xl font-semibold">{metrics.isLoading ? "…" : card.value}</p></div><card.icon className="size-7 text-cyan-600" /></CardContent></Card>)}
          </section>
          <Card className="mt-6"><CardHeader><CardTitle>{t("Platform components")}</CardTitle></CardHeader><CardContent>{components.isLoading ? <p className="text-sm text-slate-500">{t("Checking component status...")}</p> : components.isError ? <p className="text-sm text-amber-700">{t("Component status is unavailable. No healthy state is assumed.")}</p> : <div className="grid gap-3 md:grid-cols-2">{components.data?.components.map((component) => <div key={component.name} className="rounded-xl border p-4"><div className="flex items-center justify-between gap-3"><p className="font-medium">{component.name}</p><Badge variant="outline">{component.state.replaceAll("_", " ")}</Badge></div><p className="mt-2 text-xs leading-5 text-slate-500">{component.basis}</p></div>)}</div>}</CardContent></Card>
          <Card className="mt-6"><CardHeader><CardTitle>{t("Operational queues")}</CardTitle></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{components.data ? Object.entries(components.data.queues).map(([name, value]) => <div key={name} className="rounded-xl border bg-slate-50 p-4"><p className="text-xs uppercase tracking-wide text-slate-500">{name.replaceAll("_", " ")}</p><p className="mt-1 text-2xl font-semibold">{value}</p></div>) : <p className="text-sm text-slate-500">—</p>}</CardContent></Card>
          <Card className="mt-6"><CardHeader><CardTitle>{t("Observability endpoints")}</CardTitle></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2"><div className="rounded-xl border bg-slate-50 p-4"><p className="font-medium">Prometheus</p><p className="mt-1 text-sm text-slate-500">{t("Metrics collector on port 9091")}</p></div><div className="rounded-xl border bg-slate-50 p-4"><p className="font-medium">Grafana</p><p className="mt-1 text-sm text-slate-500">{t("Operational dashboards on port 3001")}</p></div></CardContent></Card>
        </main>
      </div>
    </div>
  );
}

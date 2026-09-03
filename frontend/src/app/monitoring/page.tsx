"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, Clock3, Cpu, Database, Gauge, RefreshCw } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getHealth, getPrometheusMetrics, metricSum, metricValue } from "@/lib/api/soc";

function bytes(value: number | null): string {
  return value === null ? "—" : `${(value / 1024 / 1024).toFixed(1)} MB`;
}

export default function MonitoringPage() {
  const health = useQuery({ queryKey: ["api-health"], queryFn: getHealth, refetchInterval: 15_000 });
  const metrics = useQuery({ queryKey: ["prometheus-metrics"], queryFn: getPrometheusMetrics, refetchInterval: 15_000 });
  const text = metrics.data ?? "";
  const startedAt = metricValue(text, "process_start_time_seconds");
  const cards = [
    { label: "Resident memory", value: bytes(metricValue(text, "process_resident_memory_bytes")), icon: Database },
    { label: "CPU time", value: `${metricValue(text, "process_cpu_seconds_total")?.toFixed(1) ?? "—"}s`, icon: Cpu },
    { label: "HTTP requests", value: metricSum(text, "cybersentinel_http_requests_total").toLocaleString(), icon: Gauge },
    { label: "Process uptime", value: startedAt && metrics.dataUpdatedAt ? `${Math.floor(metrics.dataUpdatedAt / 1000 - startedAt)}s` : "—", icon: Clock3 },
  ];
  const refreshing = health.isFetching || metrics.isFetching;

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-[1500px] p-5 md:p-8">
          <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700"><Activity className="size-4" />Runtime telemetry</div><h1 className="text-3xl font-semibold tracking-tight">System Monitoring</h1><p className="mt-2 text-sm text-slate-500">Live API health and Prometheus process metrics, refreshed every 15 seconds.</p></div><Button variant="outline" disabled={refreshing} onClick={() => { health.refetch(); metrics.refetch(); }}><RefreshCw className={refreshing ? "animate-spin" : ""} />Refresh</Button></header>
          <Card className={health.isSuccess ? "mb-6 border-emerald-200 bg-emerald-50" : "mb-6 border-red-200 bg-red-50"}><CardContent className="flex items-center justify-between p-5"><div><p className="font-semibold">CyberSentinel API</p><p className="mt-1 text-sm text-slate-600">{health.isSuccess ? "Health endpoint is responding normally." : health.isLoading ? "Checking service health..." : "Health check failed."}</p></div><Badge className={health.isSuccess ? "bg-emerald-600" : "bg-red-600"}>{health.isSuccess ? health.data.status.toUpperCase() : "UNAVAILABLE"}</Badge></CardContent></Card>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map((card) => <Card key={card.label}><CardContent className="flex items-center justify-between p-5"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{card.label}</p><p className="mt-2 text-2xl font-semibold">{metrics.isLoading ? "…" : card.value}</p></div><card.icon className="size-7 text-cyan-600" /></CardContent></Card>)}
          </section>
          <Card className="mt-6"><CardHeader><CardTitle>Observability endpoints</CardTitle></CardHeader><CardContent className="grid gap-3 sm:grid-cols-2"><div className="rounded-xl border bg-slate-50 p-4"><p className="font-medium">Prometheus</p><p className="mt-1 text-sm text-slate-500">Metrics collector on port 9091</p></div><div className="rounded-xl border bg-slate-50 p-4"><p className="font-medium">Grafana</p><p className="mt-1 text-sm text-slate-500">Operational dashboards on port 3001</p></div></CardContent></Card>
        </main>
      </div>
    </div>
  );
}

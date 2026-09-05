"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Clock3, RefreshCw, ShieldAlert, Siren } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getIncidents, type Incident } from "@/lib/api/incidents";
import { useSocStream } from "@/hooks/use-soc-stream";

const PAGE_SIZE = 25;
const EMPTY_INCIDENTS: Incident[] = [];
const severityStyle: Record<string, string> = {
  CRITICAL: "border-red-200 bg-red-50 text-red-700",
  HIGH: "border-orange-200 bg-orange-50 text-orange-700",
  MEDIUM: "border-amber-200 bg-amber-50 text-amber-700",
  LOW: "border-cyan-200 bg-cyan-50 text-cyan-700",
};

export default function IncidentsPage() {
  const realtimeConnected = useSocStream();
  const [page, setPage] = useState(0);
  const [status, setStatus] = useState("ALL");
  const [severity, setSeverity] = useState("ALL");
  const query = useQuery({
    queryKey: ["incidents", page],
    queryFn: () => getIncidents(PAGE_SIZE, page * PAGE_SIZE),
    refetchInterval: 30_000,
  });
  const incidents = query.data?.items ?? EMPTY_INCIDENTS;
  const filtered = useMemo(() => incidents.filter((incident) =>
    (status === "ALL" || incident.status === status) &&
    (severity === "ALL" || incident.severity === severity),
  ), [incidents, severity, status]);
  const open = incidents.filter((item) => item.status === "OPEN").length;
  const active = incidents.filter((item) => item.status === "IN_PROGRESS").length;
  const resolved = incidents.filter((item) => item.status === "RESOLVED").length;

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-[1500px] p-5 md:p-8">
          <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div><div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700"><ShieldAlert className="size-4" />Response operations</div><div className="flex items-center gap-3"><h1 className="text-3xl font-semibold tracking-tight">Incident Management</h1><Badge variant="outline" className={realtimeConnected ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-slate-200 text-slate-500"}>{realtimeConnected ? "Live" : "Reconnecting"}</Badge></div><p className="mt-2 text-sm text-slate-500">Triage, investigate and resolve incidents linked to detection evidence.</p></div>
            <div className="flex gap-2"><Button variant="outline" disabled={query.isFetching} onClick={() => query.refetch()}><RefreshCw className={query.isFetching ? "animate-spin" : ""} />Refresh</Button><Button render={<Link href="/events" />} nativeButton={false}><Siren />Review detections</Button></div>
          </header>
          <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { label: "Total incidents", value: query.data?.total ?? 0, icon: ShieldAlert, color: "text-slate-600" },
              { label: "Open", value: open, icon: Siren, color: "text-amber-600" },
              { label: "In progress", value: active, icon: Clock3, color: "text-blue-600" },
              { label: "Resolved", value: resolved, icon: CheckCircle2, color: "text-emerald-600" },
            ].map((metric) => <Card key={metric.label}><CardContent className="flex items-center justify-between p-5"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{metric.label}</p><p className="mt-2 text-3xl font-semibold">{metric.value}</p></div><metric.icon className={`size-7 ${metric.color}`} /></CardContent></Card>)}
          </section>
          <Card className="mb-6"><CardContent className="flex flex-col gap-3 p-4 sm:flex-row">
            <Select value={status} onValueChange={(value) => setStatus(value ?? "ALL")}><SelectTrigger className="w-full sm:w-52"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="ALL">All statuses</SelectItem><SelectItem value="OPEN">Open</SelectItem><SelectItem value="IN_PROGRESS">In progress</SelectItem><SelectItem value="RESOLVED">Resolved</SelectItem></SelectContent></Select>
            <Select value={severity} onValueChange={(value) => setSeverity(value ?? "ALL")}><SelectTrigger className="w-full sm:w-52"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="ALL">All severities</SelectItem><SelectItem value="CRITICAL">Critical</SelectItem><SelectItem value="HIGH">High</SelectItem><SelectItem value="MEDIUM">Medium</SelectItem><SelectItem value="LOW">Low</SelectItem></SelectContent></Select>
          </CardContent></Card>
          {query.isLoading ? <p className="py-16 text-center text-slate-500">Loading incidents...</p> : query.isError ? <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">Unable to load incidents.</p> : filtered.length === 0 ? <p className="rounded-xl border bg-white p-12 text-center text-slate-500">No incidents match the current filters.</p> : (
            <section className="space-y-3">{filtered.map((incident) => <Link key={incident.id} href={`/incidents/${incident.id}`} className="grid gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-cyan-300 hover:shadow md:grid-cols-[1fr_auto] md:items-center"><div><div className="flex flex-wrap items-center gap-2"><p className="font-semibold">{incident.title}</p><Badge variant="outline" className={severityStyle[incident.severity] ?? ""}>{incident.severity}</Badge><Badge variant="outline">{incident.status.replaceAll("_", " ")}</Badge></div><p className="mt-2 line-clamp-2 text-sm text-slate-500">{incident.description ?? "No description"}</p><p className="mt-2 text-xs text-slate-400">INC-{String(incident.id).padStart(5, "0")} · {new Date(incident.created_at).toLocaleString()} · {incident.event_count} correlated event{incident.event_count === 1 ? "" : "s"}{incident.detection_event_id ? ` · EVT-${String(incident.detection_event_id).padStart(5, "0")}` : ""}</p></div><ArrowRight className="hidden size-5 text-slate-400 md:block" /></Link>)}</section>
          )}
          <footer className="mt-6 flex items-center justify-between text-sm text-slate-500"><span>Showing {incidents.length} of {query.data?.total ?? 0} incidents</span><div className="flex gap-2"><Button variant="outline" size="sm" disabled={page === 0 || query.isFetching} onClick={() => setPage((value) => Math.max(0, value - 1))}>Previous</Button><Button variant="outline" size="sm" disabled={!query.data || (page + 1) * PAGE_SIZE >= query.data.total || query.isFetching} onClick={() => setPage((value) => value + 1)}>Next</Button></div></footer>
        </main>
      </div>
    </div>
  );
}

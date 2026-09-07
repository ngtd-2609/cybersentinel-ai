"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Clock3, RefreshCw, ShieldAlert, Siren } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getIncidentSummary, getIncidents, type Incident } from "@/lib/api/incidents";
import { useSocStream } from "@/hooks/use-soc-stream";

const PAGE_SIZE = 25;
const EMPTY_INCIDENTS: Incident[] = [];
const severityStyle: Record<string, string> = {
  CRITICAL: "border-red-200 bg-red-50 text-red-700",
  HIGH: "border-orange-200 bg-orange-50 text-orange-700",
  MEDIUM: "border-amber-200 bg-amber-50 text-amber-700",
  LOW: "border-cyan-200 bg-cyan-50 text-cyan-700",
};

function IncidentsContent() {
  const { t } = useLanguage();
  const realtimeConnected = useSocStream();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const page = Math.max(0, Number(searchParams.get("page") ?? "1") - 1);
  const status = searchParams.get("status") ?? "ALL";
  const severity = searchParams.get("severity") ?? "ALL";
  const priority = searchParams.get("priority") ?? "ALL";
  const search = searchParams.get("query") ?? "";
  const assignee = searchParams.get("assignee_user_id") ?? "";
  const asset = searchParams.get("asset_id") ?? "";
  const attackType = searchParams.get("attack_type") ?? "";
  const sourceIp = searchParams.get("source_ip") ?? "";
  const since = searchParams.get("since") ?? "";
  const until = searchParams.get("until") ?? "";
  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (!value || value === "ALL" || (key === "page" && value === "1")) params.delete(key);
    else params.set(key, value);
    if (key !== "page") params.delete("page");
    const queryString = params.toString();
    router.replace(`${pathname}${queryString ? `?${queryString}` : ""}`, { scroll: false });
  };
  const query = useQuery({
    queryKey: ["incidents", page, status, severity, priority, search, assignee, asset, attackType, sourceIp, since, until],
    queryFn: () => getIncidents(PAGE_SIZE, page * PAGE_SIZE, {
      status,
      severity,
      priority,
      query: search,
      assignee_user_id: assignee,
      asset_id: asset,
      attack_type: attackType,
      source_ip: sourceIp,
      since,
      until,
    }),
    refetchInterval: 30_000,
  });
  const summaryQuery = useQuery({
    queryKey: ["incident-summary", severity, priority, search, assignee, asset, attackType, sourceIp, since, until],
    queryFn: () => getIncidentSummary({ severity, priority, query: search, assignee_user_id: assignee, asset_id: asset, attack_type: attackType, source_ip: sourceIp, since, until }),
    refetchInterval: 30_000,
  });
  const incidents = query.data?.items ?? EMPTY_INCIDENTS;
  const summary = summaryQuery.data;

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-[1500px] p-5 md:p-8">
          <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div><div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700"><ShieldAlert className="size-4" />{t("Response operations")}</div><div className="flex items-center gap-3"><h1 className="text-3xl font-semibold tracking-tight">{t("Incident Management")}</h1><Badge variant="outline" className={realtimeConnected ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-slate-200 text-slate-500"}>{realtimeConnected ? t("Live") : t("Reconnecting")}</Badge></div><p className="mt-2 text-sm text-slate-500">{t("Triage, investigate and resolve incidents linked to detection evidence.")}</p></div>
            <div className="flex gap-2"><Button variant="outline" disabled={query.isFetching || summaryQuery.isFetching} onClick={() => { query.refetch(); summaryQuery.refetch(); }}><RefreshCw className={query.isFetching || summaryQuery.isFetching ? "animate-spin" : ""} />{t("Refresh")}</Button><Button render={<Link href="/events" />} nativeButton={false}><Siren />{t("Review detections")}</Button></div>
          </header>
          <section className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { label: "Total incidents", value: summary?.total ?? "—", icon: ShieldAlert, color: "text-slate-600" },
              { label: "Open", value: summary?.by_status.OPEN ?? "—", icon: Siren, color: "text-amber-600" },
              { label: "Active incidents", value: summary?.active ?? "—", icon: Clock3, color: "text-blue-600" },
              { label: "Resolved", value: summary?.by_status.RESOLVED ?? "—", icon: CheckCircle2, color: "text-emerald-600" },
            ].map((metric) => <Card key={metric.label}><CardContent className="flex items-center justify-between p-5"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t(metric.label)}</p><p className="mt-2 text-3xl font-semibold">{metric.value}</p></div><metric.icon className={`size-7 ${metric.color}`} /></CardContent></Card>)}
          </section>
          {summaryQuery.isError && <div className="mb-4 flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900"><span>{t("Incident totals are unavailable; the list below may still be used.")}</span><Button size="sm" variant="outline" onClick={() => summaryQuery.refetch()}>{t("Retry totals")}</Button></div>}
          {summary && <p className="mb-4 text-xs text-slate-500">Active = Open {summary.by_status.OPEN} + Investigating {summary.by_status.INVESTIGATING} + In progress {summary.by_status.IN_PROGRESS} + Contained {summary.by_status.CONTAINED}. Counts cover the full filtered dataset, not only this page.</p>}
          <Card className="mb-6"><CardContent className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-4">
            <Select value={status} onValueChange={(value) => updateFilter("status", value ?? "ALL")}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="ALL">{t("All statuses")}</SelectItem><SelectItem value="OPEN">{t("Open")}</SelectItem><SelectItem value="INVESTIGATING">{t("Investigating")}</SelectItem><SelectItem value="IN_PROGRESS">{t("In progress")}</SelectItem><SelectItem value="CONTAINED">{t("Contained")}</SelectItem><SelectItem value="RESOLVED">{t("Resolved")}</SelectItem></SelectContent></Select>
            <Select value={severity} onValueChange={(value) => updateFilter("severity", value ?? "ALL")}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="ALL">{t("All severities")}</SelectItem><SelectItem value="CRITICAL">CRITICAL</SelectItem><SelectItem value="HIGH">HIGH</SelectItem><SelectItem value="MEDIUM">MEDIUM</SelectItem><SelectItem value="LOW">LOW</SelectItem></SelectContent></Select>
            <Select value={priority} onValueChange={(value) => updateFilter("priority", value ?? "ALL")}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="ALL">{t("All priorities")}</SelectItem><SelectItem value="P1">P1</SelectItem><SelectItem value="P2">P2</SelectItem><SelectItem value="P3">P3</SelectItem><SelectItem value="P4">P4</SelectItem></SelectContent></Select>
            <Input value={search} onChange={(event) => updateFilter("query", event.target.value)} placeholder="Search case, IP, asset..." />
            <Input type="number" min={1} value={assignee} onChange={(event) => updateFilter("assignee_user_id", event.target.value)} placeholder={t("Assignee user ID")} />
            <Input value={asset} onChange={(event) => updateFilter("asset_id", event.target.value)} placeholder={t("Asset ID")} />
            <Input value={attackType} onChange={(event) => updateFilter("attack_type", event.target.value)} placeholder={t("Attack type")} />
            <Input value={sourceIp} onChange={(event) => updateFilter("source_ip", event.target.value)} placeholder={t("Source IP")} />
            <label className="grid gap-1 text-xs text-slate-500">{t("Since")}<Input type="datetime-local" value={since} onChange={(event) => updateFilter("since", event.target.value)} /></label>
            <label className="grid gap-1 text-xs text-slate-500">{t("Until")}<Input type="datetime-local" value={until} onChange={(event) => updateFilter("until", event.target.value)} /></label>
          </CardContent></Card>
          {query.isLoading ? <p className="py-16 text-center text-slate-500">{t("Loading incidents...")}</p> : query.isError ? <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">{t("Unable to load incidents. Try again.")}</p> : incidents.length === 0 ? <p className="rounded-xl border bg-white p-12 text-center text-slate-500">{t("No incidents match the current filters.")}</p> : (
            <section className="space-y-3">{incidents.map((incident) => <Link key={incident.id} href={`/incidents/${incident.id}`} className="grid gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-cyan-300 hover:shadow md:grid-cols-[1fr_auto] md:items-center"><div><div className="flex flex-wrap items-center gap-2"><p className="font-semibold">{incident.title}</p><Badge variant="outline" className={severityStyle[incident.severity] ?? ""}>{incident.severity}</Badge><Badge variant="outline">{incident.priority}</Badge><Badge variant="outline">{incident.status.replaceAll("_", " ")}</Badge></div><p className="mt-2 line-clamp-2 text-sm text-slate-500">{incident.description ?? "No description"}</p><p className="mt-2 text-xs text-slate-400">{incident.display_id ?? `INC-${String(incident.id).padStart(5, "0")}`} · {new Date(incident.created_at).toLocaleString()} · {incident.event_count} correlated event{incident.event_count === 1 ? "" : "s"}{incident.affected_assets?.[0] ? ` · ${incident.affected_assets[0].hostname}` : ""}</p></div><ArrowRight className="hidden size-5 text-slate-400 md:block" /></Link>)}</section>
          )}
          <footer className="mt-6 flex items-center justify-between text-sm text-slate-500"><span>Showing {incidents.length} of {query.data?.total ?? 0} incidents</span><div className="flex gap-2"><Button variant="outline" size="sm" disabled={page === 0 || query.isFetching} onClick={() => updateFilter("page", String(page))}>{t("Previous")}</Button><Button variant="outline" size="sm" disabled={!query.data || (page + 1) * PAGE_SIZE >= query.data.total || query.isFetching} onClick={() => updateFilter("page", String(page + 2))}>{t("Next")}</Button></div></footer>
        </main>
      </div>
    </div>
  );
}

export default function IncidentsPage() {
  return <Suspense><IncidentsContent /></Suspense>;
}

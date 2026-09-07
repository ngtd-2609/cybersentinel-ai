"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bot, Clock3, Download, Network, ShieldAlert, ShieldCheck } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  askCopilot,
  createIncidentTimeline,
  getIpThreatIntel,
  getIncidentById,
  getIncidentTimeline,
  getResponseActions,
  simulateResponse,
  updateIncident,
  updateIncidentStatus,
} from "@/lib/api/incidents";
import { canWrite } from "@/lib/auth";
import { getAdminUsers } from "@/lib/api/admin";

const statusStyle: Record<string, string> = {
  OPEN: "border-amber-200 bg-amber-50 text-amber-700",
  INVESTIGATING: "border-blue-200 bg-blue-50 text-blue-700",
  IN_PROGRESS: "border-blue-200 bg-blue-50 text-blue-700",
  CONTAINED: "border-violet-200 bg-violet-50 text-violet-700",
  RESOLVED: "border-emerald-200 bg-emerald-50 text-emerald-700",
};

export default function IncidentDetailPage() {
  const id = Number(useParams().id);
  const { user } = useAuth();
  const { t } = useLanguage();
  const queryClient = useQueryClient();
  const [action, setAction] = useState("INVESTIGATION_NOTE");
  const [note, setNote] = useState("");
  const [question, setQuestion] = useState("Assess this incident and recommend the next investigation steps.");
  const [responseAction, setResponseAction] = useState("BLOCK_SOURCE_IP");
  const [responseTarget, setResponseTarget] = useState("");
  const [newTag, setNewTag] = useState("");
  const [resolutionReason, setResolutionReason] = useState("");

  const incidentQuery = useQuery({
    queryKey: ["incident", id],
    queryFn: () => getIncidentById(id),
    enabled: Number.isFinite(id),
  });
  const timelineQuery = useQuery({
    queryKey: ["incident-timeline", id],
    queryFn: () => getIncidentTimeline(id),
    enabled: Number.isFinite(id),
  });
  const responsesQuery = useQuery({
    queryKey: ["incident-responses", id],
    queryFn: () => getResponseActions(id),
    enabled: Number.isFinite(id),
  });
  const usersQuery = useQuery({
    queryKey: ["admin-users", "incident-assignee"],
    queryFn: getAdminUsers,
    enabled: user?.role === "ADMIN",
  });

  const statusMutation = useMutation({
    mutationFn: (status: string) => updateIncidentStatus(id, status),
    onSuccess: (updated) => queryClient.setQueryData(["incident", id], updated),
  });
  const timelineMutation = useMutation({
    mutationFn: () => createIncidentTimeline(id, action, note.trim()),
    onSuccess: () => {
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["incident-timeline", id] });
    },
  });
  const priorityMutation = useMutation({
    mutationFn: (priority: string) => updateIncident(id, { priority }),
    onSuccess: (updated) => queryClient.setQueryData(["incident", id], updated),
  });
  const caseMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => updateIncident(id, payload),
    onSuccess: (updated) => {
      setResolutionReason("");
      setNewTag("");
      queryClient.setQueryData(["incident", id], updated);
      queryClient.invalidateQueries({ queryKey: ["incident-summary"] });
      queryClient.invalidateQueries({ queryKey: ["incident-timeline", id] });
    },
  });
  const responseMutation = useMutation({
    mutationFn: () => simulateResponse(id, responseAction, responseTarget.trim()),
    onSuccess: () => {
      setResponseTarget("");
      queryClient.invalidateQueries({ queryKey: ["incident-responses", id] });
      queryClient.invalidateQueries({ queryKey: ["incident-timeline", id] });
    },
  });
  const incident = incidentQuery.data;
  const mayWrite = Boolean(user && incident && (
    canWrite(user.role) ||
    (incident.workspace === "SANDBOX" && incident.owner_user_id === user.id)
  ));
  const sourceIp = incident?.detection_event?.source_ip;
  const threatIntelQuery = useQuery({
    queryKey: ["threat-intel", sourceIp],
    queryFn: () => getIpThreatIntel(sourceIp!),
    enabled: Boolean(sourceIp),
    staleTime: 300_000,
  });
  const copilotMutation = useMutation({
    mutationFn: () => askCopilot(question.trim(), JSON.stringify({
      threat_intelligence: threatIntelQuery.data ?? {
        provider: "AbuseIPDB",
        indicator: sourceIp ?? null,
        available: false,
      },
      incident: incidentQuery.data,
      timeline: timelineQuery.data ?? [],
      response_actions: responsesQuery.data ?? [],
    })),
  });
  const error = statusMutation.error ?? priorityMutation.error ?? caseMutation.error ?? timelineMutation.error ?? responseMutation.error ?? copilotMutation.error;
  const downloadReport = () => {
    if (!incident) return;
    const report = {
      generated_at: new Date().toISOString(),
      case: incident,
      threat_intelligence: threatIntelQuery.data ?? { available: false, indicator: sourceIp ?? null },
      timeline: timelineQuery.data ?? [],
      simulated_responses: responsesQuery.data ?? [],
      copilot: copilotMutation.data ?? null,
    };
    const safeJson = JSON.stringify(report, null, 2).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>${incident.display_id ?? `INC-${incident.id}`}</title><style>body{font:14px system-ui;max-width:1000px;margin:40px auto;color:#0f172a}h1{color:#0e7490}pre{white-space:pre-wrap;background:#f8fafc;border:1px solid #cbd5e1;padding:20px;border-radius:12px}</style></head><body><h1>CyberSentinel Incident Investigation Report</h1><p>Generated from authorized API responses. Response actions are simulations.</p><pre>${safeJson}</pre></body></html>`;
    const url = URL.createObjectURL(new Blob([html], { type: "text/html;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `cybersentinel-${incident.display_id ?? `incident-${incident.id}`}.html`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-[1500px] p-5 md:p-8">
          <Button render={<Link href="/incidents" />} nativeButton={false} variant="ghost" className="mb-5">
            <ArrowLeft /> {t("Back to incidents")}
          </Button>

          {incidentQuery.isLoading ? (
            <p className="py-20 text-center text-slate-500">{t("Loading incident...")}</p>
          ) : incidentQuery.isError || !incident ? (
            <p className="py-20 text-center text-red-600">{t("Unable to load this incident. Try again.")}</p>
          ) : (
            <>
              <header className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">{t("Incident response")}</p>
                  <h1 className="text-3xl font-semibold tracking-tight">{incident.title}</h1>
                  <p className="mt-2 text-sm text-slate-500">{incident.display_id ?? `INC-${String(incident.id).padStart(5, "0")}`} · Opened {new Date(incident.created_at).toLocaleString()}</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="outline" onClick={downloadReport}><Download />{t("Download investigation report")}</Button>
                  <Badge variant="outline" className={statusStyle[incident.status] ?? ""}>{incident.status.replaceAll("_", " ")}</Badge>
                  {mayWrite && (
                    <Select value={incident.status} onValueChange={(value) => value && statusMutation.mutate(value)} disabled={statusMutation.isPending}>
                      <SelectTrigger className="w-44"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="OPEN">{t("Open")}</SelectItem>
                        <SelectItem value="INVESTIGATING">{t("Investigating")}</SelectItem>
                        <SelectItem value="IN_PROGRESS">{t("In progress")}</SelectItem>
                        <SelectItem value="CONTAINED">{t("Contained")}</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </header>

              {error && <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error.message}</div>}

              <section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.8fr)]">
                <div className="space-y-6">
                  <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><ShieldAlert className="size-5 text-cyan-600" />{t("Investigation context")}</CardTitle></CardHeader>
                    <CardContent className="space-y-4 text-sm">
                      <div className="grid gap-4 sm:grid-cols-4">
                        <div><p className="text-slate-400">{t("Severity")}</p><p className="mt-1 font-semibold">{incident.severity}</p></div>
                        <div><p className="text-slate-400">{t("Status")}</p><p className="mt-1 font-semibold">{incident.status.replaceAll("_", " ")}</p></div>
                        <div><p className="text-slate-400">{t("Priority")}</p>{mayWrite ? <Select value={incident.priority} onValueChange={(value) => value && priorityMutation.mutate(value)}><SelectTrigger className="mt-1 h-8"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="P1">P1</SelectItem><SelectItem value="P2">P2</SelectItem><SelectItem value="P3">P3</SelectItem><SelectItem value="P4">P4</SelectItem></SelectContent></Select> : <p className="mt-1 font-semibold">{incident.priority}</p>}</div>
                        <div><p className="text-slate-400">{t("Detection")}</p><p className="mt-1 font-semibold">{incident.detection_event_id ? `EVT-${String(incident.detection_event_id).padStart(5, "0")}` : t("Manual")}</p></div>
                      </div>
                      <div className="grid gap-4 border-t pt-4 sm:grid-cols-2">
                        <div><p className="mb-2 text-xs font-medium text-slate-500">{t("Assignee")}</p>{mayWrite ? user?.role === "ADMIN" ? <Select value={incident.assignee_user_id ? String(incident.assignee_user_id) : "UNASSIGNED"} onValueChange={(value) => value && value !== "UNASSIGNED" && caseMutation.mutate({ assignee_user_id: Number(value) })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="UNASSIGNED" disabled>{t("Unassigned")}</SelectItem>{usersQuery.data?.filter((item) => item.is_active && item.role !== "VIEWER").map((item) => <SelectItem key={item.id} value={String(item.id)}>{item.full_name || item.username} · {item.role}</SelectItem>)}</SelectContent></Select> : <Button variant="outline" size="sm" disabled={incident.assignee_user_id === user?.id || caseMutation.isPending} onClick={() => user && caseMutation.mutate({ assignee_user_id: user.id })}>{incident.assignee_user_id === user?.id ? t("Assigned to me") : t("Assign to me")}</Button> : <p>{incident.assignee_user_id ? `User #${incident.assignee_user_id}` : t("Unassigned")}</p>}</div>
                        <div><p className="mb-2 text-xs font-medium text-slate-500">{t("Case timestamps")}</p><p className="text-xs leading-5 text-slate-600">{t("First seen")}: {incident.first_seen_at ? new Date(incident.first_seen_at).toLocaleString() : "—"}<br />{t("Last seen")}: {incident.last_event_at ? new Date(incident.last_event_at).toLocaleString() : "—"}<br />{t("Resolved at")}: {incident.resolved_at ? new Date(incident.resolved_at).toLocaleString() : "—"}</p></div>
                      </div>
                      {mayWrite && <div className="flex gap-2"><Input value={newTag} onChange={(event) => setNewTag(event.target.value)} maxLength={32} placeholder={t("Add a case tag")} /><Button variant="outline" disabled={!newTag.trim() || incident.tags.length >= 12 || caseMutation.isPending} onClick={() => caseMutation.mutate({ tags: [...new Set([...incident.tags, newTag.trim().toLowerCase()])] })}>{t("Add tag")}</Button></div>}
                      {incident.tags.length > 0 && mayWrite && <div className="flex flex-wrap gap-2">{incident.tags.map((tag) => <Button key={tag} size="sm" variant="outline" onClick={() => caseMutation.mutate({ tags: incident.tags.filter((item) => item !== tag) })}>{tag} ×</Button>)}</div>}
                      {incident.status !== "RESOLVED" && mayWrite ? <div className="space-y-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4"><p className="text-sm font-medium text-emerald-900">{t("Resolve incident")}</p><Textarea value={resolutionReason} onChange={(event) => setResolutionReason(event.target.value)} placeholder={t("Describe what was verified, contained or remediated...")} /><Button disabled={resolutionReason.trim().length < 3 || caseMutation.isPending} onClick={() => caseMutation.mutate({ status: "RESOLVED", resolution_reason: resolutionReason.trim() })}>{t("Confirm resolution")}</Button></div> : incident.status === "RESOLVED" ? <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900"><strong>{t("Resolution reason")}:</strong> {incident.resolution_reason}</div> : null}
                      <p className="border-t pt-4 leading-6 text-slate-600">{incident.description ?? t("No description provided.")}</p>
                    </CardContent>
                  </Card>

                  {incident.detection_event && (
                    <Card>
                      <CardHeader><CardTitle className="flex items-center gap-2"><Network className="size-5 text-violet-600" />{t("Detection evidence")}</CardTitle></CardHeader>
                      <CardContent className="grid gap-4 sm:grid-cols-4">
                        <div><p className="text-xs text-slate-400">{t("Threat")}</p><p className="mt-1 font-medium">{incident.detection_event.predicted_label}</p></div>
                        <div><p className="text-xs text-slate-400">{t("Source IP")}</p><p className="mt-1 font-mono text-sm">{incident.detection_event.source_ip ?? "—"}</p></div>
                        <div><p className="text-xs text-slate-400">{t("Risk score")}</p><p className="mt-1 font-semibold text-red-600">{incident.detection_event.risk_score.toFixed(0)}/100</p></div>
                        <Button render={<Link href={`/events/${incident.detection_event.id}`} />} nativeButton={false} variant="outline">{t("View event")}</Button>
                      </CardContent>
                    </Card>
                  )}

                  {(incident.affected_assets ?? []).map((asset) => (
                    <Card key={asset.id}>
                      <CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="size-5 text-emerald-600" />{t("Affected asset")}</CardTitle></CardHeader>
                      <CardContent className="grid gap-4 text-sm sm:grid-cols-3">
                        <div><p className="text-xs text-slate-400">{t("Hostname")}</p><p className="mt-1 font-semibold">{asset.hostname}</p></div>
                        <div><p className="text-xs text-slate-400">{t("Environment")}</p><p className="mt-1">{asset.environment} · {asset.criticality}</p></div>
                        <div><p className="text-xs text-slate-400">{t("Owner / exposure")}</p><p className="mt-1">{asset.owner_team ?? t("Unassigned")} · {asset.internet_facing ? t("Internet-facing") : t("Internal")}</p></div>
                        <div className="sm:col-span-3"><p className="text-xs text-slate-400">{t("System")}</p><p className="mt-1 font-mono">{asset.primary_ip ?? t("No IP")} · {asset.operating_system ?? t("Unknown OS")} · {asset.status}</p></div>
                      </CardContent>
                    </Card>
                  ))}

                  {(incident.related_detections ?? []).length > 0 && (
                    <Card>
                      <CardHeader><CardTitle>Evidence chain · {(incident.related_detections ?? []).length} detections</CardTitle></CardHeader>
                      <CardContent className="space-y-2">{(incident.related_detections ?? []).map((detection) => <Link key={detection.id} href={`/events/${detection.id}`} className="flex items-center justify-between rounded-lg border p-3 text-sm hover:border-cyan-300"><span>EVT-{String(detection.id).padStart(5, "0")} · {detection.predicted_label}</span><Badge variant="outline">{detection.severity} · {detection.risk_score.toFixed(0)}</Badge></Link>)}</CardContent>
                    </Card>
                  )}

                  {sourceIp && (
                    <Card>
                      <CardHeader><CardTitle>AbuseIPDB intelligence · {sourceIp}</CardTitle></CardHeader>
                      <CardContent className="text-sm">{threatIntelQuery.isLoading ? t("Checking AbuseIPDB...") : threatIntelQuery.isError ? <p className="text-amber-700">{t("Threat intelligence could not be loaded — local detection evidence remains usable.")}</p> : threatIntelQuery.data?.available ? <div className="grid gap-3 sm:grid-cols-4"><div><p className="text-slate-400">{t("Reputation")}</p><p className="font-semibold">{threatIntelQuery.data.reputation}</p></div><div><p className="text-slate-400">{t("Confidence")}</p><p>{threatIntelQuery.data.abuse_confidence ?? 0}%</p></div><div><p className="text-slate-400">{t("Reports / country")}</p><p>{threatIntelQuery.data.reports ?? 0} · {threatIntelQuery.data.country ?? t("Unknown")}</p></div><div><p className="text-slate-400">{t("Source")}</p><p>AbuseIPDB · {threatIntelQuery.data.cached ? t("Cached") : t("Live")}</p></div></div> : <p className="text-slate-500">{t("Provider unavailable — local detection evidence remains usable.")}</p>}</CardContent>
                    </Card>
                  )}

                  <Card>
                      <CardHeader><CardTitle className="flex items-center gap-2"><Clock3 className="size-5 text-cyan-600" />{t("Incident timeline")}</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                      {mayWrite && (
                        <div className="grid gap-3 rounded-xl border bg-slate-50 p-4 sm:grid-cols-[200px_1fr_auto]">
                          <Select value={action} onValueChange={(value) => setAction(value ?? "INVESTIGATION_NOTE")}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="INVESTIGATION_NOTE">{t("Investigation note")}</SelectItem>
                              <SelectItem value="CONTAINMENT_ACTION">{t("Containment action")}</SelectItem>
                              <SelectItem value="EVIDENCE_COLLECTED">{t("Evidence collected")}</SelectItem>
                            </SelectContent>
                          </Select>
                          <Input value={note} onChange={(event) => setNote(event.target.value)} placeholder="Describe the analyst action..." />
                          <Button disabled={!note.trim() || timelineMutation.isPending} onClick={() => timelineMutation.mutate()}>{timelineMutation.isPending ? "Adding..." : "Add entry"}</Button>
                        </div>
                      )}
                      {timelineQuery.data?.length ? timelineQuery.data.map((item) => (
                        <article key={item.id} className="border-l-2 border-cyan-200 pl-4">
                          <div className="flex flex-wrap items-center justify-between gap-2"><p className="font-medium">{item.action.replaceAll("_", " ")}</p><time className="text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</time></div>
                          <p className="mt-1 text-sm text-slate-600">{item.description}</p>
                        </article>
                      )) : <p className="text-sm text-slate-500">{t("No timeline activity yet.")}</p>}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader><CardTitle>{t("Safe active response")}</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-slate-500">{t("Portfolio actions are simulated only. No external system is modified.")}</p>
                      {mayWrite && <div className="grid gap-3 sm:grid-cols-[240px_1fr_auto]"><Select value={responseAction} onValueChange={(value) => setResponseAction(value ?? "BLOCK_SOURCE_IP")}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="BLOCK_SOURCE_IP">{t("Block source IP")}</SelectItem><SelectItem value="DISABLE_COMPROMISED_ACCOUNT">{t("Disable account")}</SelectItem><SelectItem value="ISOLATE_ASSET">{t("Isolate asset")}</SelectItem></SelectContent></Select><Input value={responseTarget} onChange={(event) => setResponseTarget(event.target.value)} placeholder={sourceIp ?? t("Target")} /><Button disabled={!responseTarget.trim() || responseMutation.isPending} onClick={() => responseMutation.mutate()}>{t("Simulate")}</Button></div>}
                      {responsesQuery.data?.map((item) => <div key={item.id} className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm"><div className="flex justify-between"><strong>{item.action.replaceAll("_", " ")}</strong><Badge variant="outline">SIMULATION</Badge></div><p className="mt-1 text-emerald-800">{item.result}</p></div>)}
                    </CardContent>
                  </Card>
                </div>

                <Card className="h-fit">
                  <CardHeader><CardTitle className="flex items-center gap-2"><Bot className="size-5 text-violet-600" />{t("SOC Copilot")}</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={4} />
                    <Button className="w-full" disabled={!question.trim() || copilotMutation.isPending} onClick={() => copilotMutation.mutate()}>{copilotMutation.isPending ? "Analyzing..." : "Analyze incident"}</Button>
                    {copilotMutation.data && (
                      <div className="space-y-4 border-t pt-4">
                        <p className="whitespace-pre-wrap text-sm leading-6 text-slate-700">{copilotMutation.data.answer}</p>
                        {copilotMutation.data.sources.map((source) => <div key={source.document_id} className="rounded-lg bg-slate-50 p-3 text-xs"><p className="font-semibold">{source.title}</p><p className="mt-1 text-slate-500">{source.source} · {(source.score * 100).toFixed(0)}%</p></div>)}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

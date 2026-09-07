"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bot, Clock3, Network, ShieldAlert, ShieldCheck } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
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
  const queryClient = useQueryClient();
  const [action, setAction] = useState("INVESTIGATION_NOTE");
  const [note, setNote] = useState("");
  const [question, setQuestion] = useState("Assess this incident and recommend the next investigation steps.");
  const [responseAction, setResponseAction] = useState("BLOCK_SOURCE_IP");
  const [responseTarget, setResponseTarget] = useState("");

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
  const error = statusMutation.error ?? priorityMutation.error ?? timelineMutation.error ?? responseMutation.error ?? copilotMutation.error;

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-[1500px] p-5 md:p-8">
          <Button render={<Link href="/incidents" />} nativeButton={false} variant="ghost" className="mb-5">
            <ArrowLeft /> Back to incidents
          </Button>

          {incidentQuery.isLoading ? (
            <p className="py-20 text-center text-slate-500">Loading incident...</p>
          ) : incidentQuery.isError || !incident ? (
            <p className="py-20 text-center text-red-600">Unable to load this incident.</p>
          ) : (
            <>
              <header className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">Incident response</p>
                  <h1 className="text-3xl font-semibold tracking-tight">{incident.title}</h1>
                  <p className="mt-2 text-sm text-slate-500">{incident.display_id ?? `INC-${String(incident.id).padStart(5, "0")}`} · Opened {new Date(incident.created_at).toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className={statusStyle[incident.status] ?? ""}>{incident.status.replaceAll("_", " ")}</Badge>
                  {mayWrite && (
                    <Select value={incident.status} onValueChange={(value) => value && statusMutation.mutate(value)} disabled={statusMutation.isPending}>
                      <SelectTrigger className="w-44"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="OPEN">Open</SelectItem>
                        <SelectItem value="INVESTIGATING">Investigating</SelectItem>
                        <SelectItem value="IN_PROGRESS">In progress</SelectItem>
                        <SelectItem value="CONTAINED">Contained</SelectItem>
                        <SelectItem value="RESOLVED">Resolved</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </header>

              {error && <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error.message}</div>}

              <section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.8fr)]">
                <div className="space-y-6">
                  <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><ShieldAlert className="size-5 text-cyan-600" />Investigation context</CardTitle></CardHeader>
                    <CardContent className="space-y-4 text-sm">
                      <div className="grid gap-4 sm:grid-cols-4">
                        <div><p className="text-slate-400">Severity</p><p className="mt-1 font-semibold">{incident.severity}</p></div>
                        <div><p className="text-slate-400">Status</p><p className="mt-1 font-semibold">{incident.status.replaceAll("_", " ")}</p></div>
                        <div><p className="text-slate-400">Priority</p>{mayWrite ? <Select value={incident.priority} onValueChange={(value) => value && priorityMutation.mutate(value)}><SelectTrigger className="mt-1 h-8"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="P1">P1</SelectItem><SelectItem value="P2">P2</SelectItem><SelectItem value="P3">P3</SelectItem><SelectItem value="P4">P4</SelectItem></SelectContent></Select> : <p className="mt-1 font-semibold">{incident.priority}</p>}</div>
                        <div><p className="text-slate-400">Detection</p><p className="mt-1 font-semibold">{incident.detection_event_id ? `EVT-${String(incident.detection_event_id).padStart(5, "0")}` : "Manual"}</p></div>
                      </div>
                      {(incident.tags ?? []).length > 0 && <div className="flex flex-wrap gap-2">{(incident.tags ?? []).map((tag) => <Badge key={tag} variant="outline">{tag}</Badge>)}</div>}
                      <p className="border-t pt-4 leading-6 text-slate-600">{incident.description ?? "No description provided."}</p>
                    </CardContent>
                  </Card>

                  {incident.detection_event && (
                    <Card>
                      <CardHeader><CardTitle className="flex items-center gap-2"><Network className="size-5 text-violet-600" />Detection evidence</CardTitle></CardHeader>
                      <CardContent className="grid gap-4 sm:grid-cols-4">
                        <div><p className="text-xs text-slate-400">Threat</p><p className="mt-1 font-medium">{incident.detection_event.predicted_label}</p></div>
                        <div><p className="text-xs text-slate-400">Source IP</p><p className="mt-1 font-mono text-sm">{incident.detection_event.source_ip ?? "—"}</p></div>
                        <div><p className="text-xs text-slate-400">Risk score</p><p className="mt-1 font-semibold text-red-600">{incident.detection_event.risk_score.toFixed(0)}/100</p></div>
                        <Button render={<Link href={`/events/${incident.detection_event.id}`} />} nativeButton={false} variant="outline">View event</Button>
                      </CardContent>
                    </Card>
                  )}

                  {(incident.affected_assets ?? []).map((asset) => (
                    <Card key={asset.id}>
                      <CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="size-5 text-emerald-600" />Affected asset</CardTitle></CardHeader>
                      <CardContent className="grid gap-4 text-sm sm:grid-cols-3">
                        <div><p className="text-xs text-slate-400">Hostname</p><p className="mt-1 font-semibold">{asset.hostname}</p></div>
                        <div><p className="text-xs text-slate-400">Environment</p><p className="mt-1">{asset.environment} · {asset.criticality}</p></div>
                        <div><p className="text-xs text-slate-400">Owner / exposure</p><p className="mt-1">{asset.owner_team ?? "Unassigned"} · {asset.internet_facing ? "Internet-facing" : "Internal"}</p></div>
                        <div className="sm:col-span-3"><p className="text-xs text-slate-400">System</p><p className="mt-1 font-mono">{asset.primary_ip ?? "No IP"} · {asset.operating_system ?? "Unknown OS"} · {asset.status}</p></div>
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
                      <CardContent className="text-sm">{threatIntelQuery.isLoading ? "Checking AbuseIPDB…" : threatIntelQuery.isError ? <p className="text-amber-700">Threat intelligence could not be loaded — local detection evidence remains usable.</p> : threatIntelQuery.data?.available ? <div className="grid gap-3 sm:grid-cols-4"><div><p className="text-slate-400">Reputation</p><p className="font-semibold">{threatIntelQuery.data.reputation}</p></div><div><p className="text-slate-400">Confidence</p><p>{threatIntelQuery.data.abuse_confidence ?? 0}%</p></div><div><p className="text-slate-400">Reports / country</p><p>{threatIntelQuery.data.reports ?? 0} · {threatIntelQuery.data.country ?? "Unknown"}</p></div><div><p className="text-slate-400">Source</p><p>AbuseIPDB{threatIntelQuery.data.cached ? " · cached" : " · live"}</p></div></div> : <p className="text-slate-500">Provider unavailable — local detection evidence remains usable.</p>}</CardContent>
                    </Card>
                  )}

                  <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><Clock3 className="size-5 text-cyan-600" />Incident timeline</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                      {mayWrite && (
                        <div className="grid gap-3 rounded-xl border bg-slate-50 p-4 sm:grid-cols-[200px_1fr_auto]">
                          <Select value={action} onValueChange={(value) => setAction(value ?? "INVESTIGATION_NOTE")}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="INVESTIGATION_NOTE">Investigation note</SelectItem>
                              <SelectItem value="CONTAINMENT_ACTION">Containment action</SelectItem>
                              <SelectItem value="EVIDENCE_COLLECTED">Evidence collected</SelectItem>
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
                      )) : <p className="text-sm text-slate-500">No timeline activity yet.</p>}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader><CardTitle>Safe active response</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-slate-500">Portfolio actions are simulated only. No external system is modified.</p>
                      {mayWrite && <div className="grid gap-3 sm:grid-cols-[240px_1fr_auto]"><Select value={responseAction} onValueChange={(value) => setResponseAction(value ?? "BLOCK_SOURCE_IP")}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="BLOCK_SOURCE_IP">Block source IP</SelectItem><SelectItem value="DISABLE_COMPROMISED_ACCOUNT">Disable account</SelectItem><SelectItem value="ISOLATE_ASSET">Isolate asset</SelectItem></SelectContent></Select><Input value={responseTarget} onChange={(event) => setResponseTarget(event.target.value)} placeholder={sourceIp ?? "Target"} /><Button disabled={!responseTarget.trim() || responseMutation.isPending} onClick={() => responseMutation.mutate()}>Simulate</Button></div>}
                      {responsesQuery.data?.map((item) => <div key={item.id} className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm"><div className="flex justify-between"><strong>{item.action.replaceAll("_", " ")}</strong><Badge variant="outline">SIMULATION</Badge></div><p className="mt-1 text-emerald-800">{item.result}</p></div>)}
                    </CardContent>
                  </Card>
                </div>

                <Card className="h-fit">
                  <CardHeader><CardTitle className="flex items-center gap-2"><Bot className="size-5 text-violet-600" />SOC Copilot</CardTitle></CardHeader>
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

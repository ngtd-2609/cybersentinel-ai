"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { createIncident } from "@/lib/api/incidents";
import { apiFetch } from "@/lib/api/client";

import { FlaskConical, RefreshCw, Search, Siren, Trash2 } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useAuth } from "@/components/auth/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DetectionEvent } from "@/lib/api/dashboard";
import { canWrite } from "@/lib/auth";
import { useSocStream } from "@/hooks/use-soc-stream";
import { resetSandbox, simulateEvent, type SimulationScenario } from "@/lib/api/soc";
import { useLanguage } from "@/components/i18n/language-provider";

interface DetectionEventPage {
  items: DetectionEvent[];
  total: number;
  limit: number;
  offset: number;
}

const PAGE_SIZE = 25;

async function getEvents(page: number, filters: Record<string, string>): Promise<DetectionEventPage> {
  const parameters = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(page * PAGE_SIZE) });
  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== "ALL") parameters.set(key, value.trim());
  });
  const response = await apiFetch(
    `/events/page?${parameters}`,
  );

  if (!response.ok) {
    throw new Error("Unable to load detection events");
  }

  return response.json() as Promise<DetectionEventPage>;
}

function severityStyle(severity: string) {
  switch (severity.toUpperCase()) {
    case "CRITICAL":
      return "border-red-200 bg-red-50 text-red-700";
    case "HIGH":
      return "border-orange-200 bg-orange-50 text-orange-700";
    case "MEDIUM":
      return "border-amber-200 bg-amber-50 text-amber-700";
    default:
      return "border-cyan-200 bg-cyan-50 text-cyan-700";
  }
}

function EventsContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { t } = useLanguage();
  const { user } = useAuth();
  const mayWrite = user ? canWrite(user.role) : false;
  const realtimeConnected = useSocStream();
  const page = Math.max(0, Number(searchParams.get("page") ?? "1") - 1);
  const search = searchParams.get("q") ?? "";
  const severity = searchParams.get("severity") ?? "ALL";
  const attackType = searchParams.get("attack_type") ?? "";
  const filterSourceIp = searchParams.get("source_ip") ?? "";
  const minRisk = searchParams.get("min_risk") ?? "";
  const maxRisk = searchParams.get("max_risk") ?? "";
  const updateFilter = (key: string, value: string) => {
    const parameters = new URLSearchParams(searchParams.toString());
    if (!value || value === "ALL" || (key === "page" && value === "1")) parameters.delete(key);
    else parameters.set(key, value);
    if (key !== "page") parameters.delete("page");
    const query = parameters.toString();
    router.replace(`${pathname}${query ? `?${query}` : ""}`, { scroll: false });
  };
  const [scenario, setScenario] = useState<SimulationScenario>("PORT-SCAN");
  const [sourceIp, setSourceIp] = useState("");
  const [hostname, setHostname] = useState("");
  const [feedback, setFeedback] = useState("");
  async function handleCreateIncident(event: DetectionEvent) {
    const incident = await createIncident({
      title: `${event.predicted_label} - EVT-${String(event.id).padStart(5, "0")}`,
      severity: event.severity,
      status: "OPEN",
      description: `Created from detection event ${event.id}`,
      detection_event_id: event.id,
    });

    router.push(`/incidents/${incident.id}`);
  }

  const {
    data,
    isLoading,
    isError,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["detection-events", page, search, severity, attackType, filterSourceIp, minRisk, maxRisk],
    queryFn: () => getEvents(page, { q: search, severity, attack_type: attackType, source_ip: filterSourceIp, min_risk: minRisk, max_risk: maxRisk }),
    refetchInterval: 30_000,
  });
  const visibleEvents = data?.items ?? [];
  const simulateMutation = useMutation({
    mutationFn: () => simulateEvent({ scenario, source_ip: sourceIp || undefined, hostname: hostname || undefined }),
    onSuccess: async (result) => {
      setFeedback(result.incident_id ? `Created EVT-${result.event.id} and INC-${result.incident_id}.` : `Created EVT-${result.event.id}.`);
      updateFilter("page", "1");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["detection-events"] }),
        queryClient.invalidateQueries({ queryKey: ["incidents"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] }),
      ]);
    },
  });
  const resetMutation = useMutation({
    mutationFn: resetSandbox,
    onSuccess: async (result) => {
      setFeedback(`Reset complete: ${result.events_deleted} events and ${result.incidents_deleted} incidents removed.`);
      updateFilter("page", "1");
      await queryClient.invalidateQueries();
    },
  });

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />

      <div className="min-w-0 flex-1">
        <Topbar />

        <main className="mx-auto max-w-[1600px] p-5 md:p-8">
          <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">
                <Siren className="size-4" />
                Security Operations
              </div>

              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-semibold tracking-tight">
                  {t("Detection Events")}
                </h1>
                <Badge variant="outline" className={realtimeConnected ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-slate-200 text-slate-500"}>
                  {realtimeConnected ? "Live" : "Reconnecting"}
                </Badge>
              </div>

              <p className="mt-2 text-sm text-slate-500">
                {t("Review intrusion detections generated by CyberSentinel AI.")}
              </p>
            </div>

            <Button
              variant="outline"
              onClick={() => refetch()}
              disabled={isFetching}
              className="w-fit"
            >
              <RefreshCw
                className={`size-4 ${
                  isFetching ? "animate-spin" : ""
                }`}
              />
              {t("Refresh")}
            </Button>
          </div>

          <Card className="mb-6 border-cyan-200 bg-gradient-to-r from-cyan-50 to-white shadow-sm">
            <CardContent className="p-5">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-end">
                <div className="xl:max-w-sm">
                  <div className="flex items-center gap-2 font-semibold"><FlaskConical className="size-5 text-cyan-700" />{t("Interactive threat simulator")}</div>
                  <p className="mt-1 text-sm text-slate-600">{t("Generate safe synthetic detections in your private sandbox. High-risk simulations automatically open an incident.")}</p>
                </div>
                <label className="grid gap-1 text-xs font-medium text-slate-600">{t("Scenario")}<Select value={scenario} onValueChange={(value) => setScenario((value ?? "PORT-SCAN") as SimulationScenario)}><SelectTrigger className="w-full bg-white xl:w-56"><SelectValue /></SelectTrigger><SelectContent>{["PORT-SCAN", "SSH-BRUTE-FORCE", "PHISHING", "RANSOMWARE", "DATA-EXFILTRATION"].map((value) => <SelectItem key={value} value={value}>{value.replaceAll("-", " ")}</SelectItem>)}</SelectContent></Select></label>
                <label className="grid gap-1 text-xs font-medium text-slate-600">{t("Source IP (optional)")}<Input value={sourceIp} onChange={(event) => setSourceIp(event.target.value)} placeholder="198.51.100.42" className="bg-white" /></label>
                <label className="grid gap-1 text-xs font-medium text-slate-600">{t("Hostname (optional)")}<Input value={hostname} onChange={(event) => setHostname(event.target.value)} placeholder="portfolio-lab" className="bg-white" /></label>
                <Button onClick={() => simulateMutation.mutate()} disabled={simulateMutation.isPending}><FlaskConical />{simulateMutation.isPending ? t("Simulating...") : t("Run simulation")}</Button>
                <Button variant="outline" onClick={() => resetMutation.mutate()} disabled={resetMutation.isPending}><Trash2 />{t("Reset my sandbox")}</Button>
              </div>
              {(feedback || simulateMutation.error || resetMutation.error) && <p role="status" className={`mt-3 text-sm ${simulateMutation.error || resetMutation.error ? "text-red-700" : "text-emerald-700"}`}>{simulateMutation.error?.message ?? resetMutation.error?.message ?? feedback}</p>}
            </CardContent>
          </Card>

          <Card className="mb-6 border-slate-200 bg-white shadow-sm">
            <CardContent className="grid gap-3 p-4 md:grid-cols-3 xl:grid-cols-6">
              <div className="relative xl:col-span-2">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />

                <Input
                  placeholder={t("Search IP, asset or attack type...")}
                  aria-label="Search detection events"
                  value={search}
                  onChange={(event) => updateFilter("q", event.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={severity} onValueChange={(value) => updateFilter("severity", value ?? "ALL")}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="ALL">{t("All severities")}</SelectItem><SelectItem value="CRITICAL">CRITICAL</SelectItem><SelectItem value="HIGH">HIGH</SelectItem><SelectItem value="MEDIUM">MEDIUM</SelectItem><SelectItem value="LOW">LOW</SelectItem></SelectContent></Select>
              <Input value={attackType} onChange={(event) => updateFilter("attack_type", event.target.value)} placeholder={t("Attack type")} />
              <Input value={filterSourceIp} onChange={(event) => updateFilter("source_ip", event.target.value)} placeholder={t("Source IP")} />
              <div className="grid grid-cols-2 gap-2"><Input type="number" min={0} max={100} value={minRisk} onChange={(event) => updateFilter("min_risk", event.target.value)} placeholder={t("Min risk")} /><Input type="number" min={0} max={100} value={maxRisk} onChange={(event) => updateFilter("max_risk", event.target.value)} placeholder={t("Max risk")} /></div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-sm">
            <CardContent className="p-0">
              {isLoading ? (
                <div className="p-10 text-center text-sm text-slate-500">
                  Loading detection events...
                </div>
              ) : isError || !data ? (
                <div className="p-10 text-center text-sm text-red-600">
                  Unable to load detection events.
                </div>
              ) : visibleEvents.length === 0 ? (
                <div className="p-10 text-center text-sm text-slate-500">
                  No detection events found.
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t("Event ID")}</TableHead>
                          <TableHead>{t("Workspace")}</TableHead>
                          <TableHead>{t("Attack Type")}</TableHead>
                          <TableHead>{t("Source IP")}</TableHead>
                          <TableHead>{t("Asset / IOC")}</TableHead>
                          <TableHead>{t("Destination")}</TableHead>
                          <TableHead>{t("Port")}</TableHead>
                          <TableHead>{t("Confidence")}</TableHead>
                          <TableHead>{t("Risk")}</TableHead>
                          <TableHead>{t("Severity")}</TableHead>
                          <TableHead>{t("Review")}</TableHead>
                        </TableRow>
                      </TableHeader>

                      <TableBody>
                        {visibleEvents.map((event) => (
                          <TableRow key={event.id}>
                            <TableCell>
                              <Link
                                href={`/events/${event.id}`}
                                className="font-mono text-xs font-semibold text-cyan-700 hover:underline"
                              >
                                EVT-{String(event.id).padStart(5, "0")}
                              </Link>
                            </TableCell>

                            <TableCell><Badge variant="outline" className={event.workspace === "SANDBOX" ? "border-violet-200 bg-violet-50 text-violet-700" : "border-slate-200 bg-slate-50 text-slate-600"}>{event.workspace === "SANDBOX" ? t("My sandbox") : t("Demo")}</Badge></TableCell>

                            <TableCell className="font-medium">
                              {event.predicted_label}
                            </TableCell>

                            <TableCell className="font-mono text-xs">
                              {event.source_ip ?? "—"}
                            </TableCell>

                            <TableCell className="text-xs">
                              <p>{event.hostname ?? event.asset_id ?? "—"}</p>
                              <p className="font-mono text-slate-400">
                                {event.ioc_value ?? "No IOC"}
                              </p>
                            </TableCell>

                            <TableCell className="font-mono text-xs">
                              {event.destination_ip ?? "—"}
                            </TableCell>

                            <TableCell>
                              {event.destination_port ?? "—"}
                            </TableCell>

                            <TableCell>
                              {(event.classifier_confidence * 100).toFixed(1)}%
                            </TableCell>

                            <TableCell className="font-semibold">
                              {event.risk_score.toFixed(0)}/100
                            </TableCell>

                            <TableCell>
                              <Badge
                                variant="outline"
                                className={severityStyle(event.severity)}
                              >
                                {event.severity}
                              </Badge>
                            </TableCell>

                            <TableCell>
                              {event.requires_review ? (
                                <Badge className="bg-violet-100 text-violet-700">
                                  Required
                                </Badge>
                              ) : (
                                <span className="text-sm text-slate-400">
                                  —
                                </span>
                              )}

                              {mayWrite && event.workspace === "SANDBOX" && (
                                <button
                                  onClick={() =>
                                    handleCreateIncident(event)
                                  }
                                  className="ml-3 rounded bg-black px-2 py-1 text-xs text-white"
                                >
                                  Create
                                </button>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="flex items-center justify-between border-t border-slate-200 px-5 py-4 text-sm text-slate-500">
                    <span>Showing {visibleEvents.length} of {data.total} events</span>
                    <div className="flex gap-2"><Button variant="outline" size="sm" disabled={page === 0 || isFetching} onClick={() => updateFilter("page", String(page))}>{t("Previous")}</Button><Button variant="outline" size="sm" disabled={(page + 1) * PAGE_SIZE >= data.total || isFetching} onClick={() => updateFilter("page", String(page + 2))}>{t("Next")}</Button></div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  );
}

export default function EventsPage() {
  return <Suspense><EventsContent /></Suspense>;
}

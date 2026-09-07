"use client";

import Link from "next/link";
import { ArrowLeft, ShieldAlert, Network, Brain, Siren } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useAuth } from "@/components/auth/auth-provider";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { createIncident, getIpThreatIntel } from "@/lib/api/incidents";
import { apiFetch } from "@/lib/api/client";
import { canWrite } from "@/lib/auth";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface DetectionEvent {
  id: number;
  source_ip: string | null;
  destination_ip: string | null;
  destination_port: number | null;
  predicted_label: string;
  classifier_confidence: number;
  anomaly_score: number;
  rule_score: number;
  risk_score: number;
  severity: string;
  requires_review: boolean;
  asset: {
    id: string;
    hostname: string;
    primary_ip: string | null;
    operating_system: string | null;
    environment: string;
    criticality: string;
    owner_team: string | null;
    internet_facing: boolean;
    status: string;
  } | null;
  created_at: string;
}

async function getEvent(
  id: string,
): Promise<DetectionEvent> {
  const response = await apiFetch(
    `/events/${id}`,
  );

  if (!response.ok) {
    throw new Error("Event not found");
  }

  return response.json() as Promise<DetectionEvent>;
}

function severityClass(severity: string) {
  switch (severity.toUpperCase()) {
    case "CRITICAL":
      return "border-red-200 bg-red-50 text-red-700";
    case "HIGH":
      return "border-orange-200 bg-orange-50 text-orange-700";
    case "MEDIUM":
      return "border-yellow-200 bg-yellow-50 text-yellow-700";
    default:
      return "border-cyan-200 bg-cyan-50 text-cyan-700";
  }
}

function ScoreCard({
  title,
  value,
}: {
  title: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">
        {title}
      </p>

      <p className="mt-2 text-2xl font-semibold text-slate-900">
        {(value * 100).toFixed(0)}%
      </p>
    </div>
  );
}

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const { t } = useLanguage();
  const mayWrite = user ? canWrite(user.role) : false;

  const id = String(params.id);

  const {
    data: event,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["event", id],
    queryFn: () => getEvent(id),
  });

  const threatIntelQuery = useQuery({
    queryKey: ["threat-intel", event?.source_ip],
    queryFn: () => getIpThreatIntel(event!.source_ip!),
    enabled: Boolean(event?.source_ip),
    staleTime: 300_000,
  });

  const createIncidentMutation = useMutation({
    mutationFn: (eventData: DetectionEvent) =>
      createIncident({
        title: `${eventData.predicted_label} - EVT-${String(eventData.id).padStart(5, "0")}`,
        severity: eventData.severity,
        status: "OPEN",
        description: `Security event from ${eventData.source_ip ?? "unknown"} to ${eventData.destination_ip ?? "unknown"}:${eventData.destination_port ?? "N/A"}`,
        detection_event_id: eventData.id,
      }),
    onSuccess: (incident) => {
      router.push(`/incidents/${incident.id}`);
    },
  });

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <div className="flex-1">
        <Topbar />

        <main className="mx-auto max-w-[1400px] p-6">
          <Link href="/events">
            <Button
              variant="ghost"
              className="mb-6"
            >
              <ArrowLeft className="size-4" />
              {t("Back to Events")}
            </Button>
          </Link>

          {isLoading && (
            <p className="text-sm text-slate-500">
              {t("Loading event...")}
            </p>
          )}

          {isError && (
            <p className="text-sm text-red-600">
              {t("Event could not be loaded. Try again.")}
            </p>
          )}

          {event && (
            <>
              <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-cyan-700">
                    <Siren className="size-4" />
                    {t("Security Investigation")}
                  </div>

                  <h1 className="text-3xl font-semibold">
                    EVT-{String(event.id).padStart(5, "0")}
                  </h1>

                  <p className="mt-2 text-sm text-slate-500">
                    {t("Detected at")}{" "}
                    {new Date(
                      event.created_at,
                    ).toLocaleString()}
                  </p>
                </div>

                <Badge
                  variant="outline"
                  className={severityClass(
                    event.severity,
                  )}
                >
                  {event.severity}
                </Badge>
              </div>


              <div className="grid gap-5 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <ShieldAlert className="size-5" />
                      {t("Threat")}
                    </CardTitle>
                  </CardHeader>

                  <CardContent>
                    <p className="text-2xl font-bold">
                      {event.predicted_label}
                    </p>

                    <p className="mt-2 text-sm text-slate-500">
                      {t("Risk score")}
                    </p>

                    <p className="text-4xl font-bold text-red-600">
                      {event.risk_score}
                    </p>
                  </CardContent>
                </Card>


                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Network className="size-5" />
                      {t("Network Flow")}
                    </CardTitle>
                  </CardHeader>

                  <CardContent className="space-y-2 text-sm">
                    <p>
                      {t("Source")}:
                      <span className="ml-2 font-mono">
                        {event.source_ip}
                      </span>
                    </p>

                    <p>
                      {t("Destination")}:
                      <span className="ml-2 font-mono">
                        {event.destination_ip}
                      </span>
                    </p>

                    <p>
                      Port:
                      <span className="ml-2 font-semibold">
                        {event.destination_port}
                      </span>
                    </p>
                  </CardContent>
                </Card>


                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Brain className="size-5" />
                      {t("AI Analysis")}
                    </CardTitle>
                  </CardHeader>

                  <CardContent className="space-y-3">
                    <ScoreCard
                      title={t("Classifier confidence")}
                      value={
                        event.classifier_confidence
                      }
                    />

                    <ScoreCard
                      title={t("Anomaly score")}
                      value={
                        event.anomaly_score
                      }
                    />

                    <ScoreCard
                      title={t("Rule score")}
                      value={
                        event.rule_score
                      }
                    />
                  </CardContent>
                </Card>
              </div>

              {event.asset && (
                <Card className="mt-5">
                  <CardHeader><CardTitle>{t("Affected asset context")}</CardTitle></CardHeader>
                  <CardContent className="grid gap-4 text-sm md:grid-cols-4">
                    <div><p className="text-slate-400">{t("Hostname")}</p><p className="font-semibold">{event.asset.hostname}</p></div>
                    <div><p className="text-slate-400">{t("System")}</p><p>{event.asset.operating_system ?? t("Unknown")}</p></div>
                    <div><p className="text-slate-400">{t("Environment")}</p><p>{event.asset.environment} · {event.asset.criticality}</p></div>
                    <div><p className="text-slate-400">{t("Ownership")}</p><p>{event.asset.owner_team ?? t("Unassigned")} · {event.asset.internet_facing ? t("Internet-facing") : t("Internal")}</p></div>
                  </CardContent>
                </Card>
              )}

              {event.source_ip && (
                <Card className="mt-5">
                  <CardHeader>
                    <CardTitle>AbuseIPDB intelligence · {event.source_ip}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm">
                    {threatIntelQuery.isLoading ? (
                      <p className="text-slate-500">{t("Checking AbuseIPDB...")}</p>
                    ) : threatIntelQuery.isError ? (
                      <p className="text-amber-700">{t("Threat intelligence could not be loaded. Local detection evidence remains available.")}</p>
                    ) : threatIntelQuery.data?.available ? (
                      <div className="grid gap-4 sm:grid-cols-4">
                        <div><p className="text-slate-400">{t("Reputation")}</p><p className="font-semibold">{threatIntelQuery.data.reputation}</p></div>
                        <div><p className="text-slate-400">{t("Abuse confidence")}</p><p className="font-semibold">{threatIntelQuery.data.abuse_confidence ?? 0}%</p></div>
                        <div><p className="text-slate-400">{t("Reports")}</p><p>{threatIntelQuery.data.reports ?? 0}</p></div>
                        <div><p className="text-slate-400">{t("Country / source")}</p><p>{threatIntelQuery.data.country ?? t("Unknown")} · AbuseIPDB{threatIntelQuery.data.cached ? ` (${t("Cached")})` : ` (${t("Live")})`}</p></div>
                      </div>
                    ) : (
                      <p className="text-slate-500">{t("AbuseIPDB is not configured or this indicator cannot be enriched. Local detection evidence remains usable.")}</p>
                    )}
                  </CardContent>
                </Card>
              )}


              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>
                    {t("Recommended response")}
                  </CardTitle>
                </CardHeader>

                <CardContent className="flex flex-wrap gap-3">
                  {mayWrite && (
                    <Button
                      variant="outline"
                      disabled={createIncidentMutation.isPending}
                      onClick={() => createIncidentMutation.mutate(event)}
                    >
                      {createIncidentMutation.isPending
                        ? t("Creating...")
                        : t("Create Incident")}
                    </Button>
                  )}

                  {event.requires_review && (
                    <Badge className="bg-violet-100 text-violet-700">
                      {t("Analyst review required")}
                    </Badge>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

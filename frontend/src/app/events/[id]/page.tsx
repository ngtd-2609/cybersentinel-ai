"use client";

import Link from "next/link";
import { ArrowLeft, ShieldAlert, Network, Brain, Siren } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { createIncident } from "@/lib/api/incidents";
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
  created_at: string;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

async function getEvent(
  id: string,
): Promise<DetectionEvent> {
  const response = await fetch(
    `${API_URL}/events/${id}`,
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

  const id = String(params.id);

  const {
    data: event,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["event", id],
    queryFn: () => getEvent(id),
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
              Back to Events
            </Button>
          </Link>

          {isLoading && (
            <p className="text-sm text-slate-500">
              Loading event...
            </p>
          )}

          {isError && (
            <p className="text-sm text-red-600">
              Event not found.
            </p>
          )}

          {event && (
            <>
              <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-cyan-700">
                    <Siren className="size-4" />
                    Security Investigation
                  </div>

                  <h1 className="text-3xl font-semibold">
                    EVT-{String(event.id).padStart(5, "0")}
                  </h1>

                  <p className="mt-2 text-sm text-slate-500">
                    Detected at{" "}
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
                      Threat
                    </CardTitle>
                  </CardHeader>

                  <CardContent>
                    <p className="text-2xl font-bold">
                      {event.predicted_label}
                    </p>

                    <p className="mt-2 text-sm text-slate-500">
                      Risk Score
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
                      Network Flow
                    </CardTitle>
                  </CardHeader>

                  <CardContent className="space-y-2 text-sm">
                    <p>
                      Source:
                      <span className="ml-2 font-mono">
                        {event.source_ip}
                      </span>
                    </p>

                    <p>
                      Destination:
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
                      AI Analysis
                    </CardTitle>
                  </CardHeader>

                  <CardContent className="space-y-3">
                    <ScoreCard
                      title="Classifier Confidence"
                      value={
                        event.classifier_confidence
                      }
                    />

                    <ScoreCard
                      title="Anomaly Score"
                      value={
                        event.anomaly_score
                      }
                    />

                    <ScoreCard
                      title="Rule Score"
                      value={
                        event.rule_score
                      }
                    />
                  </CardContent>
                </Card>
              </div>


              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>
                    Recommended Response
                  </CardTitle>
                </CardHeader>

                <CardContent className="flex flex-wrap gap-3">
                  <Button>
                    Investigate
                  </Button>

                  <Button variant="outline">
                    Block Source IP
                  </Button>

                  <Button
                    variant="outline"
                    disabled={createIncidentMutation.isPending}
                    onClick={() => createIncidentMutation.mutate(event)}
                  >
                    {createIncidentMutation.isPending
                      ? "Creating..."
                      : "Create Incident"}
                  </Button>

                  {event.requires_review && (
                    <Badge className="bg-violet-100 text-violet-700">
                      Analyst Review Required
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

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { askCopilot, getIncidentById, getIncidentTimeline, updateIncidentStatus, type Incident, type IncidentTimeline } from "@/lib/api/incidents";
import { useAuth } from "@/components/auth/auth-provider";
import { canWrite } from "@/lib/auth";


function statusClass(status: string) {
  switch (status.toUpperCase()) {
    case "RESOLVED":
      return "bg-green-100 text-green-700";
    case "IN_PROGRESS":
      return "bg-blue-100 text-blue-700";
    default:
      return "bg-yellow-100 text-yellow-700";
  }
}

export default function IncidentDetailPage() {
  const { user } = useAuth();
  const mayWrite = user ? canWrite(user.role) : false;
  const params = useParams();
  const id = Number(params.id);

  const [incident, setIncident] = useState<Incident | null>(null);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<IncidentTimeline[]>([]);
  const [copilotAnswer, setCopilotAnswer] = useState<string | null>(null);
  const [copilotSources, setCopilotSources] = useState<{ title: string; source: string; score: number }[]>([]);
  const [copilotLoading, setCopilotLoading] = useState(false);

  useEffect(() => {
    async function load() {
      const data = await getIncidentById(id);
      const history = await getIncidentTimeline(id);

      setIncident(data);
      setTimeline(history);
    }

    if (id) {
      load();
    }
  }, [id]);



  async function handleCopilot() {
    if (!incident) {
      return;
    }

    setCopilotLoading(true);

    try {
      const result = await askCopilot(
        "Analyze this security incident and provide investigation recommendations.",
        JSON.stringify({
          title: incident.title,
          severity: incident.severity,
          status: incident.status,
          description: incident.description,
          detection_event_id: incident.detection_event_id,
        }),
      );

      setCopilotAnswer(result.answer);
      setCopilotSources(result.sources);
    } catch {
      setCopilotAnswer("Unable to analyze incident.");
    } finally {
      setCopilotLoading(false);
    }
  }

  async function handleStatusChange(status: string) {
    if (!incident) {
      return;
    }

    setUpdating(true);
    setError(null);

    try {
      const updated = await updateIncidentStatus(
        incident.id,
        status,
      );

      setIncident(updated);
    } catch {
      setError("Failed to update incident status");
    } finally {
      setUpdating(false);
    }
  }

  if (!incident) {
    return (
      <main className="p-8 text-slate-500">
        Loading incident...
      </main>
    );
  }

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold">
        {incident.title}
      </h1>

      <div className="mt-6 space-y-3">

        {error && (
          <p className="text-red-600">
            {error}
          </p>
        )}
        <p>
          Severity: {incident.severity}
        </p>

        <label className="block">
          Status:
          <span
            className={`ml-3 rounded-full px-3 py-1 text-sm font-medium ${statusClass(
              incident.status,
            )}`}
          >
            {incident.status}
          </span>

          {mayWrite && (
            <select
              value={incident.status}
              disabled={updating}
              onChange={(event) =>
                handleStatusChange(event.target.value)
              }
              className="ml-3 rounded border px-3 py-2"
            >
              <option value="OPEN">OPEN</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
          )}
        </label>

        <p>
          Description: {incident.description ?? "N/A"}
        </p>

        <p>
          Detection Event ID:{" "}
          {incident.detection_event_id ? (
            <Link
              href={`/events/${incident.detection_event_id}`}
              className="text-blue-600 hover:underline"
            >
              #{incident.detection_event_id}
            </Link>
          ) : (
            "N/A"
          )}
        </p>

        <p>
          Created at: {incident.created_at}
        </p>

        <div className="mt-8 rounded-lg border p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              AI Security Copilot
            </h2>

            <button
              onClick={handleCopilot}
              disabled={copilotLoading}
              className="rounded bg-black px-3 py-2 text-white"
            >
              {copilotLoading ? "Analyzing..." : "Analyze"}
            </button>
          </div>

          {copilotAnswer && (
            <p className="whitespace-pre-line text-sm text-slate-700">
              {copilotAnswer}
            </p>
          )}

          {copilotSources.length > 0 && (
            <div className="mt-5">
              <h3 className="mb-2 font-semibold">
                Knowledge Sources
              </h3>

              <div className="space-y-2">
                {copilotSources.map((source, index) => (
                  <div
                    key={index}
                    className="rounded border p-3 text-sm"
                  >
                    <p className="font-medium">
                      {source.title}
                    </p>

                    <p className="text-slate-500">
                      {source.source}
                    </p>

                    <p className="text-xs text-cyan-700">
                      Score: {source.score.toFixed(3)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="mt-8">
          <h2 className="mb-4 text-xl font-semibold">
            Incident Timeline
          </h2>

          <div className="space-y-3">
            {timeline.length === 0 ? (
              <p className="text-slate-500">
                No timeline events.
              </p>
            ) : (
              timeline.map((item) => (
                <div
                  key={item.id}
                  className="rounded-lg border p-4"
                >
                  <p className="font-semibold">
                    {item.action}
                  </p>

                  <p className="text-sm text-slate-600">
                    {item.description}
                  </p>

                  <p className="mt-1 text-xs text-slate-400">
                    {item.created_at}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

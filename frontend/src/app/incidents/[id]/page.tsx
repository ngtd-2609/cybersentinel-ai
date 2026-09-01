"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { getIncidentById, getIncidentTimeline, updateIncidentStatus, type Incident, type IncidentTimeline } from "@/lib/api/incidents";


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
  const params = useParams();
  const id = Number(params.id);

  const [incident, setIncident] = useState<Incident | null>(null);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<IncidentTimeline[]>([]);

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

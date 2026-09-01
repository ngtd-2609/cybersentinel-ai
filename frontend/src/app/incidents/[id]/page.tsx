"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { getIncidentById, type Incident } from "@/lib/api/incidents";

export default function IncidentDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const [incident, setIncident] = useState<Incident | null>(null);

  useEffect(() => {
    async function load() {
      const data = await getIncidentById(id);
      setIncident(data);
    }

    if (id) {
      load();
    }
  }, [id]);

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
        <p>
          Severity: {incident.severity}
        </p>

        <p>
          Status: {incident.status}
        </p>

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
      </div>
    </main>
  );
}

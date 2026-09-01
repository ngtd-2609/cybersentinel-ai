"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  createIncident,
  getIncidents,
  type Incident,
} from "@/lib/api/incidents";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");

  async function loadIncidents() {
    const data = await getIncidents();
    setIncidents(data);
    setLoading(false);
  }

  useEffect(() => {
    let mounted = true;

    getIncidents().then((data) => {
      if (mounted) {
        setIncidents(data);
        setLoading(false);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  async function handleCreate() {
    await createIncident({
      title: "New Security Incident",
      severity: "HIGH",
      status: "OPEN",
      description: "Created from analyst dashboard",
    });

    loadIncidents();
  }

  const filteredIncidents = incidents.filter((incident) => {
    const matchStatus =
      statusFilter === "ALL" ||
      incident.status === statusFilter;

    const matchSeverity =
      severityFilter === "ALL" ||
      incident.severity === severityFilter;

    return matchStatus && matchSeverity;
  });

  return (
    <main className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          Incident Management
        </h1>

        <button
          onClick={handleCreate}
          className="rounded-lg bg-black px-4 py-2 text-white"
        >
          Create Incident
        </button>
      </div>

      <div className="mb-6 flex gap-3">
        <select
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(event.target.value)
          }
          className="rounded border px-3 py-2"
        >
          <option value="ALL">All Status</option>
          <option value="OPEN">OPEN</option>
          <option value="IN_PROGRESS">IN_PROGRESS</option>
          <option value="RESOLVED">RESOLVED</option>
        </select>

        <select
          value={severityFilter}
          onChange={(event) =>
            setSeverityFilter(event.target.value)
          }
          className="rounded border px-3 py-2"
        >
          <option value="ALL">All Severity</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : filteredIncidents.length === 0 ? (
        <p>No incidents found.</p>
      ) : (
        <div className="space-y-3">
          {filteredIncidents.map((incident) => (
            <Link
              key={incident.id}
              href={`/incidents/${incident.id}`}
              className="block rounded-lg border p-4 transition hover:bg-slate-50"
            >
              <div className="flex justify-between">
                <h2 className="font-semibold">
                  {incident.title}
                </h2>

                <span>
                  {incident.severity}
                </span>
              </div>

              <p className="text-sm text-gray-500">
                {incident.status}
              </p>

              <p className="mt-2">
                {incident.description}
              </p>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}

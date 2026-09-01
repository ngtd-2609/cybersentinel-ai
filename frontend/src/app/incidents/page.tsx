"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

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
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);

  const loadIncidents = useCallback(
    async (currentPage = page) => {
      setLoading(true);

      const data = await getIncidents(
        25,
        currentPage * 25,
      );

      setIncidents(data.items);
      setTotal(data.total);
      setLoading(false);
    },
    [page],
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      loadIncidents(page);
    }, 0);

    return () => {
      clearTimeout(timer);
    };
  }, [loadIncidents, page]);

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


  const summary = {
    total: incidents.length,
    open: incidents.filter(
      (incident) => incident.status === "OPEN",
    ).length,
    progress: incidents.filter(
      (incident) => incident.status === "IN_PROGRESS",
    ).length,
    resolved: incidents.filter(
      (incident) => incident.status === "RESOLVED",
    ).length,
    critical: incidents.filter(
      (incident) => incident.severity === "CRITICAL",
    ).length,
  };

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


      <div className="mb-6 grid gap-4 md:grid-cols-5">
        <div className="rounded-lg border p-4">
          <p className="text-sm text-slate-500">
            Total
          </p>
          <p className="text-2xl font-bold">
            {summary.total}
          </p>
        </div>

        <div className="rounded-lg border p-4">
          <p className="text-sm text-slate-500">
            Open
          </p>
          <p className="text-2xl font-bold text-yellow-600">
            {summary.open}
          </p>
        </div>

        <div className="rounded-lg border p-4">
          <p className="text-sm text-slate-500">
            In Progress
          </p>
          <p className="text-2xl font-bold text-blue-600">
            {summary.progress}
          </p>
        </div>

        <div className="rounded-lg border p-4">
          <p className="text-sm text-slate-500">
            Resolved
          </p>
          <p className="text-2xl font-bold text-green-600">
            {summary.resolved}
          </p>
        </div>

        <div className="rounded-lg border p-4">
          <p className="text-sm text-slate-500">
            Critical
          </p>
          <p className="text-2xl font-bold text-red-600">
            {summary.critical}
          </p>
        </div>
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


      <div className="mt-6 flex items-center justify-between">
        <p className="text-sm text-slate-500">
          Showing {incidents.length} of {total} incidents
        </p>

        <div className="flex gap-3">
          <button
            disabled={page === 0}
            onClick={() =>
              setPage((current) => Math.max(current - 1, 0))
            }
            className="rounded border px-3 py-2 disabled:opacity-50"
          >
            Previous
          </button>

          <button
            disabled={(page + 1) * 25 >= total}
            onClick={() =>
              setPage((current) => current + 1)
            }
            className="rounded border px-3 py-2 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>

    </main>
  );
}

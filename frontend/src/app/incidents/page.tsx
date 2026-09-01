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

      {loading ? (
        <p>Loading...</p>
      ) : incidents.length === 0 ? (
        <p>No incidents found.</p>
      ) : (
        <div className="space-y-3">
          {incidents.map((incident) => (
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

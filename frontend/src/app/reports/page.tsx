"use client";

import { useQuery } from "@tanstack/react-query";
import { Download, FileBarChart, FileText, ShieldCheck } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDashboardSummary } from "@/lib/api/dashboard";
import { getIncidents } from "@/lib/api/incidents";
import { downloadCsv, getDetectionEvents, summaryToRows } from "@/lib/api/soc";

const stamp = () => new Date().toISOString().slice(0, 10);

export default function ReportsPage() {
  const summary = useQuery({ queryKey: ["dashboard-summary"], queryFn: getDashboardSummary });
  const events = useQuery({ queryKey: ["report-events"], queryFn: () => getDetectionEvents(100) });
  const incidents = useQuery({ queryKey: ["report-incidents"], queryFn: () => getIncidents(100, 0) });

  const reports = [
    {
      title: "Executive security summary",
      description: "High-level alert volume, severity and risk posture.",
      icon: FileBarChart,
      count: summary.data ? "6 metrics" : "Loading",
      disabled: !summary.data,
      download: () => summary.data && downloadCsv(`cybersentinel-summary-${stamp()}.csv`, summaryToRows(summary.data)),
    },
    {
      title: "Detection event export",
      description: "Latest 100 detections with network, confidence and risk evidence.",
      icon: ShieldCheck,
      count: events.data ? `${events.data.items.length} records` : "Loading",
      disabled: !events.data,
      download: () => events.data && downloadCsv(`cybersentinel-events-${stamp()}.csv`, [
        ["ID", "Created", "Attack", "Source IP", "Destination IP", "Port", "Confidence", "Risk", "Severity", "Review"],
        ...events.data.items.map((event) => [String(event.id), event.created_at, event.predicted_label, event.source_ip ?? "", event.destination_ip ?? "", String(event.destination_port ?? ""), String(event.classifier_confidence), String(event.risk_score), event.severity, String(event.requires_review)]),
      ]),
    },
    {
      title: "Incident response register",
      description: "Latest 100 incidents, workflow state and linked detection IDs.",
      icon: FileText,
      count: incidents.data ? `${incidents.data.items.length} records` : "Loading",
      disabled: !incidents.data,
      download: () => incidents.data && downloadCsv(`cybersentinel-incidents-${stamp()}.csv`, [
        ["ID", "Created", "Title", "Severity", "Status", "Detection Event", "Description"],
        ...incidents.data.items.map((incident) => [String(incident.id), incident.created_at, incident.title, incident.severity, incident.status, String(incident.detection_event_id ?? ""), incident.description ?? ""]),
      ]),
    },
  ];
  const hasError = summary.isError || events.isError || incidents.isError;

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-6xl p-5 md:p-8">
          <header className="mb-8"><p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">Operational exports</p><h1 className="text-3xl font-semibold tracking-tight">Reports</h1><p className="mt-2 text-sm text-slate-500">Generate CSV reports directly from current CyberSentinel API data.</p></header>
          {hasError && <p role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">One or more report datasets could not be loaded.</p>}
          <section className="grid gap-5 lg:grid-cols-3">
            {reports.map((report) => <Card key={report.title} className="flex flex-col"><CardHeader><div className="mb-3 flex size-11 items-center justify-center rounded-xl bg-cyan-50"><report.icon className="size-5 text-cyan-600" /></div><CardTitle className="text-lg">{report.title}</CardTitle><p className="text-sm leading-6 text-slate-500">{report.description}</p></CardHeader><CardContent className="mt-auto"><div className="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-400">{report.count}</div><Button className="w-full" disabled={report.disabled} onClick={report.download}><Download />Download CSV</Button></CardContent></Card>)}
          </section>
          <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500">Exports are generated in your browser from authorized API responses. No report data is sent to another service.</div>
        </main>
      </div>
    </div>
  );
}

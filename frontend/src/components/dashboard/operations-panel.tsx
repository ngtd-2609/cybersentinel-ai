import Link from "next/link";
import {
  ArrowRight,
  Bot,
  BrainCircuit,
  Clock3,
  Search,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const incidents = [
  {
    id: "INC-0241",
    title: "Distributed Port Scanning",
    severity: "Critical",
    events: 18,
    status: "Investigating",
    updated: "4 min ago",
  },
  {
    id: "INC-0240",
    title: "SSH Brute Force Campaign",
    severity: "High",
    events: 11,
    status: "Triaged",
    updated: "17 min ago",
  },
  {
    id: "INC-0239",
    title: "Abnormal Web Traffic",
    severity: "Medium",
    events: 7,
    status: "Contained",
    updated: "38 min ago",
  },
];

function severityClass(severity: string) {
  if (severity === "Critical") {
    return "border-red-200 bg-red-50 text-red-700";
  }

  if (severity === "High") {
    return "border-orange-200 bg-orange-50 text-orange-700";
  }

  return "border-amber-200 bg-amber-50 text-amber-700";
}

export function OperationsPanel() {
  return (
    <section className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(340px,0.8fr)]">
      <Card className="border-slate-200 bg-white shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="size-4 text-cyan-600" />
              <CardTitle className="text-base">
                Active Incidents
              </CardTitle>
            </div>

            <p className="mt-1 text-sm text-slate-500">
              Correlated security events currently under analyst review.
            </p>
          </div>

          <Link
            href="/incidents"
            className="flex items-center gap-1 text-sm font-medium text-cyan-700 hover:text-cyan-800"
          >
            View incidents
            <ArrowRight className="size-4" />
          </Link>
        </CardHeader>

        <CardContent className="space-y-3">
          {incidents.map((incident) => (
            <Link
              key={incident.id}
              href={`/incidents/${incident.id}`}
              className="flex flex-col gap-4 rounded-xl border border-slate-200 p-4 transition hover:border-cyan-200 hover:bg-cyan-50/30 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-cyan-700">
                    {incident.id}
                  </span>

                  <Badge
                    variant="outline"
                    className={severityClass(incident.severity)}
                  >
                    {incident.severity}
                  </Badge>
                </div>

                <p className="mt-2 font-medium text-slate-900">
                  {incident.title}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {incident.events} correlated events
                </p>
              </div>

              <div className="flex shrink-0 items-center gap-5">
                <div>
                  <p className="text-xs font-medium text-slate-700">
                    {incident.status}
                  </p>

                  <p className="mt-1 flex items-center gap-1 text-xs text-slate-400">
                    <Clock3 className="size-3" />
                    {incident.updated}
                  </p>
                </div>

                <ArrowRight className="size-4 text-slate-400" />
              </div>
            </Link>
          ))}
        </CardContent>
      </Card>

      <Card className="border-cyan-200 bg-gradient-to-br from-cyan-50 via-white to-sky-50 shadow-sm">
        <CardHeader>
          <div className="flex size-10 items-center justify-center rounded-xl bg-cyan-100">
            <Bot className="size-5 text-cyan-700" />
          </div>

          <CardTitle className="mt-3 text-base">
            SOC Copilot
          </CardTitle>

          <p className="text-sm leading-6 text-slate-500">
            Investigate events using detection evidence, MITRE ATT&CK context
            and threat intelligence.
          </p>
        </CardHeader>

        <CardContent>
          <div className="space-y-2">
            <Link
              href="/copilot"
              className="flex items-center gap-3 rounded-xl border border-cyan-100 bg-white p-3 text-sm font-medium text-slate-700 transition hover:border-cyan-300 hover:text-cyan-800"
            >
              <Search className="size-4 text-cyan-600" />
              Analyze critical alerts
            </Link>

            <Link
              href="/copilot"
              className="flex items-center gap-3 rounded-xl border border-cyan-100 bg-white p-3 text-sm font-medium text-slate-700 transition hover:border-cyan-300 hover:text-cyan-800"
            >
              <BrainCircuit className="size-4 text-cyan-600" />
              Explain risk scoring
            </Link>

            <Link
              href="/copilot"
              className="flex items-center gap-3 rounded-xl border border-cyan-100 bg-white p-3 text-sm font-medium text-slate-700 transition hover:border-cyan-300 hover:text-cyan-800"
            >
              <Sparkles className="size-4 text-cyan-600" />
              Recommend response actions
            </Link>
          </div>

          <Button className="mt-4 w-full bg-cyan-600 text-white hover:bg-cyan-700">
            <Bot className="size-4" />
            Open SOC Copilot
          </Button>
        </CardContent>
      </Card>
    </section>
  );
}

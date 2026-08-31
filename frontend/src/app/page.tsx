import {
  Activity,
  AlertTriangle,
  Ban,
  Crosshair,
  ShieldAlert,
  Siren,
} from "lucide-react";

import { AttackTypesChart } from "@/components/dashboard/attack-types-chart";
import { SecurityEventsChart } from "@/components/dashboard/security-events-chart";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const metrics = [
  {
    label: "Total Events",
    value: "12,842",
    change: "+8.2%",
    description: "Last 24 hours",
    icon: Activity,
  },
  {
    label: "Active Threats",
    value: "37",
    change: "+4",
    description: "Currently under analysis",
    icon: Siren,
  },
  {
    label: "Critical Alerts",
    value: "18",
    change: "-12.4%",
    description: "Requires immediate attention",
    icon: AlertTriangle,
  },
  {
    label: "High Alerts",
    value: "64",
    change: "+5.1%",
    description: "High-risk detections",
    icon: ShieldAlert,
  },
  {
    label: "Threats Blocked",
    value: "1,284",
    change: "+21.7%",
    description: "Automated response",
    icon: Ban,
  },
  {
    label: "Average Risk Score",
    value: "37.8",
    change: "-4.1%",
    description: "Across all events",
    icon: Crosshair,
  },
];

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />

      <div className="min-w-0 flex-1">
        <Topbar />

        <main className="mx-auto max-w-[1600px] p-5 md:p-8">
          <section className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="mb-2 flex items-center gap-2">
                <span className="size-2 rounded-full bg-emerald-500" />

                <span className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">
                  Live Security Operations
                </span>
              </div>

              <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
                Security Overview
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                Monitor security events, active threats, risk scores and
                detection activity across CyberSentinel AI.
              </p>
            </div>

            <Badge
              variant="outline"
              className="w-fit border-cyan-200 bg-cyan-50 px-3 py-1.5 text-cyan-700"
            >
              Production Mode
            </Badge>
          </section>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
            {metrics.map((metric) => (
              <Card
                key={metric.label}
                className="border-slate-200 bg-white shadow-sm"
              >
                <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
                  <div className="flex size-10 items-center justify-center rounded-xl bg-cyan-50">
                    <metric.icon className="size-5 text-cyan-600" />
                  </div>

                  <span className="text-xs font-semibold text-slate-500">
                    {metric.change}
                  </span>
                </CardHeader>

                <CardContent>
                  <CardTitle className="text-sm font-medium text-slate-500">
                    {metric.label}
                  </CardTitle>

                  <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
                    {metric.value}
                  </p>

                  <p className="mt-2 text-xs text-slate-400">
                    {metric.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
            <Card className="min-h-[390px] border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">
                  Security Events Over Time
                </CardTitle>

                <p className="text-sm text-slate-500">
                  Event volume and severity trend will be connected to the
                  backend in the next steps.
                </p>
              </CardHeader>

              <CardContent>
                <SecurityEventsChart />
              </CardContent>
            </Card>

            <Card className="min-h-[390px] border-slate-200 bg-white shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">
                  Top Attack Types
                </CardTitle>

                <p className="text-sm text-slate-500">
                  Highest-frequency attack categories.
                </p>
              </CardHeader>

              <CardContent>
                <AttackTypesChart />
              </CardContent>
            </Card>
          </section>
        </main>
      </div>
    </div>
  );
}

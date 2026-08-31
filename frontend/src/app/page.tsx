import { AttackTypesChart } from "@/components/dashboard/attack-types-chart";
import { LiveMetrics } from "@/components/dashboard/live-metrics";
import { OperationsPanel } from "@/components/dashboard/operations-panel";
import { SecurityEventsChart } from "@/components/dashboard/security-events-chart";
import { SecurityInsights } from "@/components/dashboard/security-insights";
import { RecentAlerts } from "@/components/dashboard/recent-alerts";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";



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

          <LiveMetrics />

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

          <section className="mt-6">
            <RecentAlerts />
          </section>

          <SecurityInsights />

          <OperationsPanel />
        </main>
      </div>
    </div>
  );
}

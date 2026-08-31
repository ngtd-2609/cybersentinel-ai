"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Globe2,
  Network,
  ShieldCheck,
} from "lucide-react";

import { SeverityDistribution } from "@/components/dashboard/severity-distribution";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";



const pipeline = [
  {
    name: "Binary XGBoost",
    detail: "Intrusion detection",
  },
  {
    name: "Multiclass XGBoost",
    detail: "Attack classification",
  },
  {
    name: "Isolation Forest",
    detail: "Anomaly detection",
  },
  {
    name: "Risk Engine",
    detail: "Risk prioritization",
  },
];

export function SecurityInsights() {
  const { data, isLoading } = useDashboardSummary();
  const topSources = data?.top_threat_sources ?? [];

  return (
    <section className="mt-6 grid gap-6 xl:grid-cols-3">
      <Card className="border-slate-200 bg-white shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">
            Severity Distribution
          </CardTitle>

          <p className="text-sm text-slate-500">
            Distribution of prioritized security alerts.
          </p>
        </CardHeader>

        <CardContent>
          <SeverityDistribution />
        </CardContent>
      </Card>

      <Card className="border-slate-200 bg-white shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Globe2 className="size-4 text-cyan-600" />

            <CardTitle className="text-base">
              Top Threat Sources
            </CardTitle>
          </div>

          <p className="text-sm text-slate-500">
            Source IPs generating the highest-risk activity.
          </p>
        </CardHeader>

        <CardContent className="space-y-4">
          {isLoading ? (
            Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-11 w-full" />
            ))
          ) : topSources.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-400">
              No threat source data available.
            </p>
          ) : (
            topSources.map((source, index) => (
              <div
                key={source.source_ip}
                className="flex items-center justify-between gap-4"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-xs font-semibold text-slate-500">
                    {index + 1}
                  </div>

                  <div className="min-w-0">
                    <p className="truncate font-mono text-xs font-medium text-slate-800">
                      {source.source_ip}
                    </p>

                    <p className="mt-0.5 text-xs text-slate-400">
                      {source.count} detection events
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <p className="text-sm font-semibold text-slate-900">
                    {source.max_risk_score.toFixed(0)}
                  </p>

                  <p className="text-[10px] uppercase tracking-wide text-slate-400">
                    Max Risk
                  </p>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-orange-500" />

              <CardTitle className="text-base">
                Threat Level
              </CardTitle>
            </div>
          </CardHeader>

          <CardContent>
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-2xl font-semibold text-orange-600">
                  Elevated
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-500">
                  Increased scanning activity detected across monitored
                  services.
                </p>
              </div>

              <div className="rounded-full bg-orange-50 px-3 py-1 text-xs font-semibold text-orange-700">
                Level 3/5
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Network className="size-4 text-cyan-600" />

              <CardTitle className="text-base">
                Network Coverage
              </CardTitle>
            </div>
          </CardHeader>

          <CardContent>
            <div className="flex items-end justify-between">
              <p className="text-3xl font-semibold tracking-tight">
                98.7%
              </p>

              <p className="text-xs font-medium text-emerald-600">
                Healthy
              </p>
            </div>

            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full w-[98.7%] rounded-full bg-cyan-500" />
            </div>

            <p className="mt-2 text-xs text-slate-400">
              148 of 150 monitored assets reporting
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-200 bg-white shadow-sm xl:col-span-3">
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-emerald-600" />

            <CardTitle className="text-base">
              Detection Pipeline
            </CardTitle>
          </div>

          <p className="text-sm text-slate-500">
            Operational status of AI detection and risk services.
          </p>
        </CardHeader>

        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {pipeline.map((service) => (
              <div
                key={service.name}
                className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50/60 p-4"
              >
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    {service.name}
                  </p>

                  <p className="mt-1 text-xs text-slate-400">
                    {service.detail}
                  </p>
                </div>

                <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-600">
                  <CheckCircle2 className="size-4" />
                  Operational
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

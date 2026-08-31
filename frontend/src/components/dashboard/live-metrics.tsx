"use client";

import {
  Activity,
  AlertTriangle,
  Crosshair,
  Eye,
  ShieldAlert,
  Siren,
} from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";

export function LiveMetrics() {
  const { data, isLoading, isError } = useDashboardSummary();

  if (isLoading) {
    return (
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <Card key={index} className="border-slate-200 bg-white shadow-sm">
            <CardContent className="space-y-3 p-5">
              <Skeleton className="size-10 rounded-xl" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-3 w-28" />
            </CardContent>
          </Card>
        ))}
      </section>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Unable to load live security metrics from the CyberSentinel API.
      </div>
    );
  }

  const metrics = [
    {
      label: "Total Events",
      value: data.total_events.toLocaleString(),
      description: "Stored detection events",
      icon: Activity,
    },
    {
      label: "Active Threats",
      value: data.requires_review.toLocaleString(),
      description: "Requires analyst review",
      icon: Siren,
    },
    {
      label: "Critical Alerts",
      value: data.critical_alerts.toLocaleString(),
      description: "Critical severity",
      icon: AlertTriangle,
    },
    {
      label: "High Alerts",
      value: data.high_alerts.toLocaleString(),
      description: "High severity",
      icon: ShieldAlert,
    },
    {
      label: "Medium + Low",
      value: (data.medium_alerts + data.low_alerts).toLocaleString(),
      description: "Lower-priority detections",
      icon: Eye,
    },
    {
      label: "Average Risk Score",
      value: data.average_risk_score.toFixed(1),
      description: "Across stored events",
      icon: Crosshair,
    },
  ];

  return (
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

            <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-600">
              <span className="size-1.5 rounded-full bg-emerald-500" />
              LIVE
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
  );
}

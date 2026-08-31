"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";

function severityStyle(severity: string) {
  switch (severity.toUpperCase()) {
    case "CRITICAL":
      return "border-red-200 bg-red-50 text-red-700";
    case "HIGH":
      return "border-orange-200 bg-orange-50 text-orange-700";
    case "MEDIUM":
      return "border-amber-200 bg-amber-50 text-amber-700";
    default:
      return "border-cyan-200 bg-cyan-50 text-cyan-700";
  }
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function RecentAlerts() {
  const { data, isLoading, isError } = useDashboardSummary();

  return (
    <Card className="border-slate-200 bg-white shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-base">
            Recent Detection Events
          </CardTitle>

          <p className="mt-1 text-sm text-slate-500">
            Latest events returned by the CyberSentinel detection API.
          </p>
        </div>

        <Link
          href="/events"
          className="inline-flex h-8 items-center justify-center gap-1 rounded-md px-3 text-sm font-medium text-cyan-700 transition hover:bg-cyan-50 hover:text-cyan-800"
        >
          View all
          <ChevronRight className="size-4" />
        </Link>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-12 w-full" />
            ))}
          </div>
        ) : isError || !data ? (
          <div className="py-10 text-center text-sm text-red-600">
            Unable to load recent detection events.
          </div>
        ) : data.recent_events.length === 0 ? (
          <div className="py-10 text-center text-sm text-slate-400">
            No detection events available.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Event</TableHead>
                  <TableHead>Attack Type</TableHead>
                  <TableHead>Source IP</TableHead>
                  <TableHead>Destination</TableHead>
                  <TableHead>Risk</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Review</TableHead>
                  <TableHead className="text-right">Time</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {data.recent_events.slice(0, 8).map((event) => (
                  <TableRow key={event.id}>
                    <TableCell>
                      <Link
                        href={`/events/${event.id}`}
                        className="font-mono text-xs font-medium text-cyan-700 hover:underline"
                      >
                        EVT-{String(event.id).padStart(5, "0")}
                      </Link>
                    </TableCell>

                    <TableCell className="font-medium text-slate-800">
                      {event.predicted_label}
                    </TableCell>

                    <TableCell className="font-mono text-xs text-slate-600">
                      {event.source_ip ?? "—"}
                    </TableCell>

                    <TableCell className="font-mono text-xs text-slate-600">
                      {event.destination_ip ?? "—"}
                    </TableCell>

                    <TableCell>
                      <span className="font-semibold text-slate-950">
                        {event.risk_score.toFixed(0)}
                      </span>
                      <span className="text-slate-400">/100</span>
                    </TableCell>

                    <TableCell>
                      <Badge
                        variant="outline"
                        className={severityStyle(event.severity)}
                      >
                        {event.severity}
                      </Badge>
                    </TableCell>

                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          event.requires_review
                            ? "border-violet-200 bg-violet-50 text-violet-700"
                            : "border-emerald-200 bg-emerald-50 text-emerald-700"
                        }
                      >
                        {event.requires_review ? "Required" : "Not required"}
                      </Badge>
                    </TableCell>

                    <TableCell className="text-right text-xs text-slate-500">
                      {formatTime(event.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

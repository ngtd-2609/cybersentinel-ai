"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";

export function SecurityEventsChart() {
  const { data, isLoading, isError } = useDashboardSummary();

  if (isLoading) {
    return <Skeleton className="h-[290px] w-full rounded-xl" />;
  }

  if (isError || !data) {
    return (
      <div className="flex h-[290px] items-center justify-center text-sm text-red-600">
        Unable to load security event timeline.
      </div>
    );
  }

  const chartData = data.timeline.map((point) => ({
    ...point,
    label: new Intl.DateTimeFormat("en", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(point.time)),
  }));

  return (
    <div className="h-[290px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData}>
          <defs>
            <linearGradient
              id="eventsGradient"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="5%"
                stopColor="#06b6d4"
                stopOpacity={0.28}
              />
              <stop
                offset="95%"
                stopColor="#06b6d4"
                stopOpacity={0}
              />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="#e2e8f0"
          />

          <XAxis
            dataKey="label"
            axisLine={false}
            tickLine={false}
            minTickGap={30}
            tick={{
              fill: "#94a3b8",
              fontSize: 11,
            }}
          />

          <YAxis
            allowDecimals={false}
            axisLine={false}
            tickLine={false}
            tick={{
              fill: "#94a3b8",
              fontSize: 11,
            }}
          />

          <Tooltip
            contentStyle={{
              borderRadius: "12px",
              border: "1px solid #e2e8f0",
              boxShadow:
                "0 10px 30px rgba(15,23,42,0.08)",
            }}
          />

          <Area
            type="monotone"
            dataKey="total"
            name="Total Events"
            stroke="#06b6d4"
            strokeWidth={2}
            fill="url(#eventsGradient)"
          />

          <Line
            type="monotone"
            dataKey="critical"
            name="Critical"
            stroke="#ef4444"
            strokeWidth={2}
            dot={false}
          />

          <Line
            type="monotone"
            dataKey="high"
            name="High"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

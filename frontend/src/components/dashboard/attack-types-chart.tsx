"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";

export function AttackTypesChart() {
  const { data, isLoading, isError } = useDashboardSummary();

  if (isLoading) {
    return <Skeleton className="h-[290px] w-full rounded-xl" />;
  }

  if (isError || !data) {
    return (
      <div className="flex h-[290px] items-center justify-center text-sm text-red-600">
        Unable to load attack statistics.
      </div>
    );
  }

  if (data.top_attack_types.length === 0) {
    return (
      <div className="flex h-[290px] items-center justify-center text-sm text-slate-400">
        No attack data available.
      </div>
    );
  }

  return (
    <div className="h-[290px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data.top_attack_types}
          layout="vertical"
          margin={{ left: 12, right: 12 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            horizontal={false}
            stroke="#e2e8f0"
          />

          <XAxis
            type="number"
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
            tick={{ fill: "#94a3b8", fontSize: 12 }}
          />

          <YAxis
            type="category"
            dataKey="name"
            width={95}
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#64748b", fontSize: 12 }}
          />

          <Tooltip
            cursor={{ fill: "#f8fafc" }}
            contentStyle={{
              borderRadius: "12px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 10px 30px rgba(15,23,42,0.08)",
            }}
          />

          <Bar
            dataKey="count"
            name="Events"
            fill="#06b6d4"
            radius={[0, 6, 6, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardSummary } from "@/hooks/use-dashboard-summary";

export function SeverityDistribution() {
  const { data, isLoading, isError } = useDashboardSummary();

  if (isLoading) {
    return <Skeleton className="h-[290px] w-full rounded-xl" />;
  }

  if (isError || !data) {
    return (
      <div className="flex h-[290px] items-center justify-center text-sm text-red-600">
        Unable to load severity data.
      </div>
    );
  }

  const chartData = [
    {
      name: "Critical",
      value: data.critical_alerts,
      color: "#ef4444",
    },
    {
      name: "High",
      value: data.high_alerts,
      color: "#f97316",
    },
    {
      name: "Medium",
      value: data.medium_alerts,
      color: "#f59e0b",
    },
    {
      name: "Low",
      value: data.low_alerts,
      color: "#06b6d4",
    },
  ];

  const hasData = chartData.some((item) => item.value > 0);

  if (!hasData) {
    return (
      <div className="flex h-[290px] items-center justify-center text-sm text-slate-400">
        No severity data available.
      </div>
    );
  }

  return (
    <div className="h-[290px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="45%"
            innerRadius={62}
            outerRadius={96}
            paddingAngle={3}
          >
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>

          <Tooltip
            contentStyle={{
              borderRadius: "12px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 10px 30px rgba(15,23,42,0.08)",
            }}
          />

          <Legend
            verticalAlign="bottom"
            iconType="circle"
            iconSize={8}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

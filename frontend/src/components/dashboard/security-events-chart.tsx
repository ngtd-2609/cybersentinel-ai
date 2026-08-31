"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const data = [
  { time: "00:00", events: 420, critical: 7 },
  { time: "04:00", events: 610, critical: 12 },
  { time: "08:00", events: 980, critical: 19 },
  { time: "12:00", events: 1340, critical: 27 },
  { time: "16:00", events: 1180, critical: 21 },
  { time: "20:00", events: 1540, critical: 31 },
  { time: "24:00", events: 1280, critical: 18 },
];

export function SecurityEventsChart() {
  return (
    <div className="h-[290px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="eventsGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.28} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="#e2e8f0"
          />

          <XAxis
            dataKey="time"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#94a3b8", fontSize: 12 }}
          />

          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#94a3b8", fontSize: 12 }}
          />

          <Tooltip
            contentStyle={{
              borderRadius: "12px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 10px 30px rgba(15,23,42,0.08)",
            }}
          />

          <Area
            type="monotone"
            dataKey="events"
            stroke="#06b6d4"
            strokeWidth={2}
            fill="url(#eventsGradient)"
          />

          <Area
            type="monotone"
            dataKey="critical"
            stroke="#ef4444"
            strokeWidth={2}
            fill="transparent"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

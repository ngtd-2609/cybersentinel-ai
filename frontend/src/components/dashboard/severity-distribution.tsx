"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const data = [
  { name: "Critical", value: 18, color: "#ef4444" },
  { name: "High", value: 64, color: "#f97316" },
  { name: "Medium", value: 186, color: "#f59e0b" },
  { name: "Low", value: 412, color: "#06b6d4" },
];

export function SeverityDistribution() {
  return (
    <div className="h-[290px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="45%"
            innerRadius={62}
            outerRadius={96}
            paddingAngle={3}
          >
            {data.map((entry) => (
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

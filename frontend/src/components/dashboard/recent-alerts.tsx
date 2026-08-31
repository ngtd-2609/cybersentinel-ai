import { ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const alerts = [
  {
    id: "EVT-18429",
    time: "2 min ago",
    type: "PortScan",
    source: "185.220.101.14",
    destination: "10.0.4.21",
    risk: 94,
    severity: "Critical",
    status: "New",
  },
  {
    id: "EVT-18428",
    time: "8 min ago",
    type: "DDoS",
    source: "45.83.64.17",
    destination: "10.0.8.14",
    risk: 88,
    severity: "High",
    status: "Investigating",
  },
  {
    id: "EVT-18427",
    time: "14 min ago",
    type: "SSH-Patator",
    source: "91.92.240.32",
    destination: "10.0.2.8",
    risk: 76,
    severity: "High",
    status: "Triaged",
  },
  {
    id: "EVT-18426",
    time: "21 min ago",
    type: "Web Attack",
    source: "103.14.26.51",
    destination: "10.0.5.12",
    risk: 62,
    severity: "Medium",
    status: "Investigating",
  },
];

function severityStyle(severity: string) {
  if (severity === "Critical") {
    return "border-red-200 bg-red-50 text-red-700";
  }

  if (severity === "High") {
    return "border-orange-200 bg-orange-50 text-orange-700";
  }

  return "border-amber-200 bg-amber-50 text-amber-700";
}

export function RecentAlerts() {
  return (
    <Card className="border-slate-200 bg-white shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-base">
            Recent High-Risk Alerts
          </CardTitle>

          <p className="mt-1 text-sm text-slate-500">
            Latest detections prioritized by the CyberSentinel risk engine.
          </p>
        </div>

        <Button
          variant="ghost"
          size="sm"
          className="text-cyan-700 hover:bg-cyan-50 hover:text-cyan-800"
        >
          View all
          <ChevronRight className="size-4" />
        </Button>
      </CardHeader>

      <CardContent>
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
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Time</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {alerts.map((alert) => (
                <TableRow key={alert.id}>
                  <TableCell className="font-mono text-xs font-medium text-cyan-700">
                    {alert.id}
                  </TableCell>

                  <TableCell className="font-medium text-slate-800">
                    {alert.type}
                  </TableCell>

                  <TableCell className="font-mono text-xs text-slate-600">
                    {alert.source}
                  </TableCell>

                  <TableCell className="font-mono text-xs text-slate-600">
                    {alert.destination}
                  </TableCell>

                  <TableCell>
                    <span className="font-semibold text-slate-950">
                      {alert.risk}
                    </span>
                    <span className="text-slate-400">/100</span>
                  </TableCell>

                  <TableCell>
                    <Badge
                      variant="outline"
                      className={severityStyle(alert.severity)}
                    >
                      {alert.severity}
                    </Badge>
                  </TableCell>

                  <TableCell>
                    <Badge
                      variant="outline"
                      className="border-slate-200 bg-slate-50 text-slate-600"
                    >
                      {alert.status}
                    </Badge>
                  </TableCell>

                  <TableCell className="text-right text-xs text-slate-500">
                    {alert.time}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileClock, FilterX, RefreshCw, ScrollText } from "lucide-react";

import { AdminGuard } from "@/components/auth/admin-guard";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getAuditLogs } from "@/lib/api/admin";

const PAGE_SIZE = 25;

const ACTIONS = [
  "ALL",
  "LOGIN_SUCCESS",
  "LOGIN_FAILED",
  "LOGIN_BLOCKED",
  "CREATE_USER",
  "UPDATE_ROLE",
  "UPDATE_STATUS",
  "CREATE_DETECTION_EVENT",
  "CREATE_INCIDENT",
  "CREATE_INCIDENT_FROM_DETECTION",
  "UPDATE_INCIDENT_STATUS",
  "CREATE_INCIDENT_TIMELINE",
];

function formatAction(action: string): string {
  return action
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function AuditLogsPanel() {
  const [page, setPage] = useState(0);
  const [action, setAction] = useState("ALL");
  const [targetType, setTargetType] = useState("ALL");
  const [userId, setUserId] = useState("");
  const parsedUserId = /^\d+$/.test(userId) ? Number(userId) : undefined;

  const auditQuery = useQuery({
    queryKey: ["audit-logs", page, action, targetType, parsedUserId],
    queryFn: () =>
      getAuditLogs({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        action: action === "ALL" ? undefined : action,
        targetType: targetType === "ALL" ? undefined : targetType,
        userId: parsedUserId,
      }),
  });

  const data = auditQuery.data;
  const hasFilters = action !== "ALL" || targetType !== "ALL" || userId !== "";

  function resetFilters() {
    setAction("ALL");
    setTargetType("ALL");
    setUserId("");
    setPage(0);
  }

  return (
    <main className="mx-auto max-w-[1600px] p-5 md:p-8">
      <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">
            <ScrollText className="size-4" />
            Security accountability
          </div>
          <h1 className="text-3xl font-semibold tracking-tight">Audit Logs</h1>
          <p className="mt-2 text-sm text-slate-500">
            Review authentication, administration and incident activity.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => auditQuery.refetch()}
          disabled={auditQuery.isFetching}
        >
          <RefreshCw
            className={`size-4 ${auditQuery.isFetching ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </header>

      <section className="mb-6 grid gap-4 sm:grid-cols-2">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Matching records
              </p>
              <p className="mt-2 text-3xl font-semibold">{data?.total ?? "—"}</p>
            </div>
            <FileClock className="size-7 text-cyan-600" />
          </CardContent>
        </Card>
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Current page
              </p>
              <p className="mt-2 text-3xl font-semibold">{page + 1}</p>
            </div>
            <ScrollText className="size-7 text-violet-600" />
          </CardContent>
        </Card>
      </section>

      <Card className="mb-6 border-slate-200 bg-white shadow-sm">
        <CardContent className="grid gap-3 p-4 md:grid-cols-[1fr_1fr_1fr_auto]">
          <Select
            value={action}
            onValueChange={(value) => {
              setAction(value ?? "ALL");
              setPage(0);
            }}
          >
            <SelectTrigger className="h-9 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ACTIONS.map((item) => (
                <SelectItem key={item} value={item}>
                  {item === "ALL" ? "All actions" : formatAction(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={targetType}
            onValueChange={(value) => {
              setTargetType(value ?? "ALL");
              setPage(0);
            }}
          >
            <SelectTrigger className="h-9 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All target types</SelectItem>
              <SelectItem value="USER">User</SelectItem>
              <SelectItem value="DETECTION_EVENT">Detection event</SelectItem>
              <SelectItem value="INCIDENT">Incident</SelectItem>
            </SelectContent>
          </Select>

          <Input
            inputMode="numeric"
            value={userId}
            onChange={(event) => {
              setUserId(event.target.value.replace(/\D/g, ""));
              setPage(0);
            }}
            placeholder="Actor user ID"
          />

          <Button
            variant="outline"
            onClick={resetFilters}
            disabled={!hasFilters}
          >
            <FilterX className="size-4" />
            Reset
          </Button>
        </CardContent>
      </Card>

      <Card className="border-slate-200 bg-white shadow-sm">
        <CardContent className="p-0">
          {auditQuery.isLoading ? (
            <p className="p-10 text-center text-sm text-slate-500">
              Loading audit records...
            </p>
          ) : auditQuery.isError ? (
            <p className="p-10 text-center text-sm text-red-600">
              {auditQuery.error.message}
            </p>
          ) : !data || data.items.length === 0 ? (
            <p className="p-10 text-center text-sm text-slate-500">
              No audit records match the current filters.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="px-5">Timestamp</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead className="pr-5">Description</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="px-5 py-4 text-xs text-slate-500">
                      {new Date(log.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-cyan-200 bg-cyan-50 text-cyan-700">
                        {formatAction(log.action)}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {log.user_id ? `User #${log.user_id}` : "System"}
                    </TableCell>
                    <TableCell className="text-xs text-slate-600">
                      {log.target_type
                        ? `${formatAction(log.target_type)}${log.target_id ? ` #${log.target_id}` : ""}`
                        : "—"}
                    </TableCell>
                    <TableCell className="max-w-xl whitespace-normal pr-5 text-sm text-slate-600">
                      {log.description}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          <footer className="flex flex-col gap-3 border-t border-slate-200 px-5 py-4 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <span>
              Showing {data?.items.length ?? 0} of {data?.total ?? 0} records
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 0 || auditQuery.isFetching}
                onClick={() => setPage((current) => Math.max(0, current - 1))}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={
                  auditQuery.isFetching ||
                  !data ||
                  (page + 1) * PAGE_SIZE >= data.total
                }
                onClick={() => setPage((current) => current + 1)}
              >
                Next
              </Button>
            </div>
          </footer>
        </CardContent>
      </Card>
    </main>
  );
}

export default function AuditLogsPage() {
  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <AdminGuard>
          <AuditLogsPanel />
        </AdminGuard>
      </div>
    </div>
  );
}

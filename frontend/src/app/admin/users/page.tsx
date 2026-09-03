"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  RefreshCw,
  Search,
  ShieldCheck,
  UserCheck,
  Users,
  UserX,
} from "lucide-react";

import { AdminGuard } from "@/components/auth/admin-guard";
import { useAuth } from "@/components/auth/auth-provider";
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
import {
  getAdminUsers,
  updateAdminUserRole,
  updateAdminUserStatus,
  USER_ROLES,
  type AdminUser,
} from "@/lib/api/admin";
import { formatRole } from "@/lib/auth";

const EMPTY_USERS: AdminUser[] = [];

function UsersPanel() {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("ALL");

  const usersQuery = useQuery({
    queryKey: ["admin-users"],
    queryFn: getAdminUsers,
  });

  function updateCachedUser(updated: AdminUser) {
    queryClient.setQueryData<AdminUser[]>(
      ["admin-users"],
      (current = []) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
    );
  }

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: string }) =>
      updateAdminUserRole(userId, role),
    onSuccess: updateCachedUser,
  });

  const statusMutation = useMutation({
    mutationFn: ({ userId, isActive }: { userId: number; isActive: boolean }) =>
      updateAdminUserStatus(userId, isActive),
    onSuccess: updateCachedUser,
  });

  const users = usersQuery.data ?? EMPTY_USERS;
  const filteredUsers = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return users.filter((user) => {
      const matchesSearch =
        !normalizedSearch ||
        user.email.toLowerCase().includes(normalizedSearch) ||
        user.username.toLowerCase().includes(normalizedSearch) ||
        user.full_name?.toLowerCase().includes(normalizedSearch);
      const matchesRole = roleFilter === "ALL" || user.role === roleFilter;
      return matchesSearch && matchesRole;
    });
  }, [roleFilter, search, users]);

  const activeCount = users.filter((user) => user.is_active).length;
  const privilegedCount = users.filter((user) => user.role !== "VIEWER").length;
  const mutationError = roleMutation.error ?? statusMutation.error;

  return (
    <main className="mx-auto max-w-[1600px] p-5 md:p-8">
      <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">
            <ShieldCheck className="size-4" />
            Access governance
          </div>
          <h1 className="text-3xl font-semibold tracking-tight">Users & Roles</h1>
          <p className="mt-2 text-sm text-slate-500">
            Manage SOC access levels and account availability.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => usersQuery.refetch()}
          disabled={usersQuery.isFetching}
        >
          <RefreshCw
            className={`size-4 ${usersQuery.isFetching ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </header>

      <section className="mb-6 grid gap-4 sm:grid-cols-3">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Total users
              </p>
              <p className="mt-2 text-3xl font-semibold">{users.length}</p>
            </div>
            <Users className="size-7 text-cyan-600" />
          </CardContent>
        </Card>
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Active accounts
              </p>
              <p className="mt-2 text-3xl font-semibold">{activeCount}</p>
            </div>
            <UserCheck className="size-7 text-emerald-600" />
          </CardContent>
        </Card>
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardContent className="flex items-center justify-between p-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Elevated roles
              </p>
              <p className="mt-2 text-3xl font-semibold">{privilegedCount}</p>
            </div>
            <ShieldCheck className="size-7 text-violet-600" />
          </CardContent>
        </Card>
      </section>

      <Card className="mb-6 border-slate-200 bg-white shadow-sm">
        <CardContent className="flex flex-col gap-3 p-4 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search name, username or email..."
              className="pl-10"
            />
          </div>
          <Select value={roleFilter} onValueChange={(value) => setRoleFilter(value ?? "ALL")}>
            <SelectTrigger className="h-9 w-full sm:w-52">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All roles</SelectItem>
              {USER_ROLES.map((role) => (
                <SelectItem key={role} value={role}>
                  {formatRole(role)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {mutationError && (
        <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {mutationError.message}
        </div>
      )}

      <Card className="border-slate-200 bg-white shadow-sm">
        <CardContent className="p-0">
          {usersQuery.isLoading ? (
            <p className="p-10 text-center text-sm text-slate-500">Loading users...</p>
          ) : usersQuery.isError ? (
            <p className="p-10 text-center text-sm text-red-600">
              {usersQuery.error.message}
            </p>
          ) : filteredUsers.length === 0 ? (
            <p className="p-10 text-center text-sm text-slate-500">
              No users match the current filters.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="px-5">User</TableHead>
                  <TableHead>Username</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="pr-5 text-right">Account control</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => {
                  const isCurrentUser = user.id === currentUser?.id;
                  const rolePending =
                    roleMutation.isPending && roleMutation.variables?.userId === user.id;
                  const statusPending =
                    statusMutation.isPending && statusMutation.variables?.userId === user.id;

                  return (
                    <TableRow key={user.id} className={isCurrentUser ? "bg-cyan-50/50" : undefined}>
                      <TableCell className="px-5 py-4">
                        <div>
                          <p className="font-medium text-slate-950">
                            {user.full_name ?? user.email}
                            {isCurrentUser && (
                              <Badge variant="outline" className="ml-2 border-cyan-200 bg-cyan-50 text-cyan-700">
                                You
                              </Badge>
                            )}
                          </p>
                          <p className="mt-1 text-xs text-slate-500">{user.email}</p>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-xs">{user.username}</TableCell>
                      <TableCell>
                        <Select
                          value={user.role}
                          disabled={isCurrentUser || rolePending}
                          onValueChange={(role) => {
                            if (role && role !== user.role) {
                              roleMutation.mutate({ userId: user.id, role });
                            }
                          }}
                        >
                          <SelectTrigger className="w-44">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {USER_ROLES.map((role) => (
                              <SelectItem key={role} value={role}>
                                {formatRole(role)}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            user.is_active
                              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                              : "border-slate-200 bg-slate-100 text-slate-600"
                          }
                        >
                          {user.is_active ? "Active" : "Disabled"}
                        </Badge>
                      </TableCell>
                      <TableCell className="pr-5 text-right">
                        <Button
                          variant={user.is_active ? "destructive" : "outline"}
                          size="sm"
                          disabled={isCurrentUser || statusPending}
                          title={isCurrentUser ? "You cannot disable your own account" : undefined}
                          onClick={() =>
                            statusMutation.mutate({
                              userId: user.id,
                              isActive: !user.is_active,
                            })
                          }
                        >
                          {user.is_active ? <UserX /> : <UserCheck />}
                          {statusPending
                            ? "Updating..."
                            : user.is_active
                              ? "Disable"
                              : "Enable"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
          <div className="border-t border-slate-200 px-5 py-4 text-sm text-slate-500">
            Showing {filteredUsers.length} of {users.length} users
          </div>
        </CardContent>
      </Card>
    </main>
  );
}

export default function UsersPage() {
  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <AdminGuard>
          <UsersPanel />
        </AdminGuard>
      </div>
    </div>
  );
}

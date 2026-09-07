"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, ShieldCheck } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getAlertRules, updateAlertRule, type AlertRule } from "@/lib/api/rules";

export default function RulesPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["alert-rules"], queryFn: getAlertRules });
  const mutation = useMutation({
    mutationFn: ({ id, enabled }: Pick<AlertRule, "id" | "enabled">) => updateAlertRule(id, { enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alert-rules"] }),
  });
  const mayEdit = user?.role === "ADMIN";

  return <div className="flex min-h-screen bg-slate-50 text-slate-950"><Sidebar /><div className="min-w-0 flex-1"><Topbar /><main className="mx-auto max-w-[1500px] p-5 md:p-8">
    <header className="mb-8 flex items-end justify-between gap-4"><div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">{t("Detection policy")}</p><h1 className="text-3xl font-semibold">{t("Detection Rules")}</h1><p className="mt-2 text-sm text-slate-500">{t("Rules evaluate stored event fields: severity, risk, review requirement and label pattern.")}</p></div><Button variant="outline" onClick={() => query.refetch()} disabled={query.isFetching}><RefreshCw className={query.isFetching ? "animate-spin" : ""} />{t("Refresh")}</Button></header>
    {!mayEdit && <p className="mb-5 rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">{t("You have read-only access to detection rules.")}</p>}
    {mutation.isError && <p role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{t("The rule could not be updated. Try again.")}</p>}
    {query.isLoading ? <p className="py-16 text-center text-slate-500">{t("Loading detection rules...")}</p> : query.isError ? <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">{t("Detection rules are unavailable. Existing detections are not being reclassified.")}</div> : !query.data?.length ? <p className="rounded-xl border bg-white p-12 text-center text-slate-500">{t("No detection rules are configured.")}</p> : <section className="grid gap-4 lg:grid-cols-2">{query.data.map((rule) => <Card key={rule.id}><CardContent className="space-y-4 p-5"><div className="flex items-start justify-between gap-4"><div><h2 className="flex items-center gap-2 font-semibold"><ShieldCheck className="size-4 text-cyan-600" />{rule.name}</h2><p className="mt-1 text-xs text-slate-500">{t("Priority")} {rule.priority} · {t("Updated")} {new Date(rule.updated_at).toLocaleString()}</p></div><Button size="sm" variant={rule.enabled ? "default" : "outline"} disabled={!mayEdit || mutation.isPending} onClick={() => mutation.mutate({ id: rule.id, enabled: !rule.enabled })}>{rule.enabled ? t("Enabled") : t("Disabled")}</Button></div><div className="flex flex-wrap gap-2"><Badge variant="outline">{t("Minimum risk")} {rule.min_risk_score}</Badge>{rule.severities.map((severity) => <Badge key={severity} variant="outline">{severity}</Badge>)}<Badge variant="outline">{rule.label_pattern ?? t("Any label")}</Badge></div><div className="grid grid-cols-2 gap-3 text-xs text-slate-600"><p>{t("Requires review")}: <strong>{rule.require_review ? t("Yes") : t("No")}</strong></p><p>{t("Auto incident")}: <strong>{rule.auto_create_incident ? t("Yes") : t("No")}</strong></p><p>{t("Notifications")}: <strong>{rule.notification_channels.length ? rule.notification_channels.join(", ") : t("None")}</strong></p><p>{t("Last triggered")}: <strong>{t("Not tracked")}</strong></p></div></CardContent></Card>)}</section>}
  </main></div></div>;
}

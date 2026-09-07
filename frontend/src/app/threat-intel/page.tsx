"use client";

import { useQueries, useQuery } from "@tanstack/react-query";
import { Crosshair, Globe2, Radar, RefreshCw, ShieldAlert } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDashboardSummary } from "@/lib/api/dashboard";
import { getIpThreatIntel, type ThreatIntel } from "@/lib/api/incidents";

const techniques: Record<string, { id: string; name: string }> = {
  RANSOMWARE: { id: "T1486", name: "Data Encrypted for Impact" },
  "SSH-BRUTE-FORCE": { id: "T1110", name: "Brute Force" },
  "PORT-SCAN": { id: "T1046", name: "Network Service Discovery" },
  PHISHING: { id: "T1566", name: "Phishing" },
  "DATA-EXFILTRATION": { id: "T1041", name: "Exfiltration Over C2 Channel" },
  "C2-TRAFFIC": { id: "T1071", name: "Application Layer Protocol" },
  "WEB-ATTACK": { id: "T1190", name: "Exploit Public-Facing Application" },
  "BRUTE-FORCE": { id: "T1110", name: "Brute Force" },
  MALWARE: { id: "—", name: "Malware behavior" },
};

export default function ThreatIntelPage() {
  const { t } = useLanguage();
  const query = useQuery({ queryKey: ["dashboard-summary"], queryFn: getDashboardSummary });
  const data = query.data;
  const sources = data?.top_threat_sources.slice(0, 5) ?? [];
  const enrichments = useQueries({
    queries: sources.map((source) => ({
      queryKey: ["threat-intel", source.source_ip],
      queryFn: () => getIpThreatIntel(source.source_ip),
      staleTime: 5 * 60_000,
      retry: 1,
    })),
  });

  const stateLabel = (intel: ThreatIntel | undefined, pending: boolean, failed: boolean) => {
    if (pending) return "Checking";
    if (failed || !intel) return "Temporarily unavailable";
    if (!intel.available) return intel.error?.toLowerCase().includes("not configured") ? "Provider not configured" : "Temporarily unavailable";
    return intel.cached ? "Cached" : "Live";
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-[1500px] p-5 md:p-8">
          <header className="mb-8 flex items-end justify-between gap-4"><div><div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700"><Radar className="size-4" />{t("Observed intelligence")}</div><h1 className="text-3xl font-semibold tracking-tight">{t("Threat Intelligence")}</h1><p className="mt-2 text-sm text-slate-500">{t("Local detection evidence enriched on demand for the five most-observed source IPs.")}</p></div><Button variant="outline" disabled={query.isFetching} onClick={() => query.refetch()}><RefreshCw className={query.isFetching ? "animate-spin" : ""} />{t("Refresh sources")}</Button></header>
          {query.isLoading ? <p className="py-20 text-center text-slate-500">{t("Loading threat intelligence...")}</p> : query.isError || !data ? <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700"><p>{t("Threat sources could not be loaded. No current result is being inferred.")}</p><Button className="mt-3" variant="outline" onClick={() => query.refetch()}>{t("Retry")}</Button></div> : (
            <div className="grid gap-6 xl:grid-cols-2">
              <Card className="xl:col-span-2">
                <CardHeader><CardTitle className="flex items-center gap-2"><Globe2 className="size-5 text-cyan-600" />{t("Observed source indicators")}</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                  {sources.length ? <table className="w-full min-w-[980px] text-left text-sm"><thead className="border-b text-xs uppercase tracking-wide text-slate-500"><tr><th className="p-3">Indicator</th><th className="p-3">{t("Local evidence")}</th><th className="p-3">{t("Provider")}</th><th className="p-3">{t("Reputation")}</th><th className="p-3">{t("Confidence")}</th><th className="p-3">{t("Reports")}</th><th className="p-3">{t("Country")}</th><th className="p-3">{t("State / checked")}</th></tr></thead><tbody>{sources.map((source, index) => {
                    const result = enrichments[index];
                    const intel = result.data;
                    const state = stateLabel(intel, result.isPending, result.isError);
                    const stateClass = state === "Live" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : state === "Cached" ? "border-blue-200 bg-blue-50 text-blue-700" : state === "Checking" ? "border-slate-200 bg-slate-50 text-slate-600" : "border-amber-200 bg-amber-50 text-amber-800";
                    return <tr key={source.source_ip} className="border-b last:border-0"><td className="p-3 font-mono font-semibold">{source.source_ip}</td><td className="p-3"><span className="font-medium">{t("Risk")} {source.max_risk_score.toFixed(0)}</span><br /><span className="text-xs text-slate-500">{source.count} {t("sightings")}</span></td><td className="p-3">{intel?.provider ?? "AbuseIPDB"}</td><td className="p-3 font-medium">{intel?.available ? intel.reputation.replaceAll("_", " ") : t("Not confirmed")}</td><td className="p-3">{intel?.available && intel.abuse_confidence !== null ? `${intel.abuse_confidence}%` : "—"}</td><td className="p-3">{intel?.available && intel.reports !== null ? intel.reports : "—"}</td><td className="p-3">{intel?.available ? (intel.country ?? t("Unknown")) : "—"}</td><td className="p-3"><Badge variant="outline" className={stateClass}>{t(state)}</Badge><p className="mt-1 text-xs text-slate-500">{intel?.checked_at ? new Date(intel.checked_at).toLocaleString() : t("Awaiting provider")}</p>{(result.isError || intel?.available === false) && <Button className="mt-2 h-7 px-2 text-xs" variant="outline" onClick={() => result.refetch()}>{t("Retry")}</Button>}</td></tr>;
                  })}</tbody></table> : <p className="text-sm text-slate-500">{t("No source indicators have been observed. This does not mean the external provider found no threats.")}</p>}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><Crosshair className="size-5 text-violet-600" />{t("Attack techniques")}</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {data.top_attack_types.map((attack) => {
                    const technique = techniques[attack.name.toUpperCase()] ?? { id: "—", name: "Unmapped observed behavior" };
                    return <article key={attack.name} className="rounded-xl border p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{attack.name}</p><p className="mt-1 text-sm text-slate-500">{technique.id} · {technique.name}</p></div><Badge>{attack.count} events</Badge></div></article>;
                  })}
                  {!data.top_attack_types.length && <p className="text-sm text-slate-500">{t("No attack patterns observed.")}</p>}
                </CardContent>
              </Card>
              <Card className="xl:col-span-2"><CardContent className="flex items-start gap-4 p-5"><ShieldAlert className="mt-0.5 size-5 text-amber-600" /><div><p className="font-medium">{t("How to read this page")}</p><p className="mt-1 text-sm leading-6 text-slate-500">{t("Local risk comes from CyberSentinel detections; AbuseIPDB reputation is separate external evidence. Abuse confidence is not model confidence, and a MITRE mapping is contextual—not proof of attacker attribution. Provider failure never becomes a safe or low-risk result.")}</p></div></CardContent></Card>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

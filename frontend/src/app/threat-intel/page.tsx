"use client";

import { useQuery } from "@tanstack/react-query";
import { Crosshair, Globe2, Radar, ShieldAlert } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDashboardSummary } from "@/lib/api/dashboard";

const techniques: Record<string, { id: string; name: string }> = {
  RANSOMWARE: { id: "T1486", name: "Data Encrypted for Impact" },
  "SSH-BRUTE-FORCE": { id: "T1110", name: "Brute Force" },
  "BRUTE-FORCE": { id: "T1110", name: "Brute Force" },
  MALWARE: { id: "—", name: "Malware behavior" },
};

export default function ThreatIntelPage() {
  const query = useQuery({ queryKey: ["dashboard-summary"], queryFn: getDashboardSummary });
  const data = query.data;

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-[1500px] p-5 md:p-8">
          <header className="mb-8"><div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700"><Radar className="size-4" />Observed intelligence</div><h1 className="text-3xl font-semibold tracking-tight">Threat Intelligence</h1><p className="mt-2 text-sm text-slate-500">Prioritize observed adversary sources and attack techniques from live detections.</p></header>
          {query.isLoading ? <p className="py-20 text-center text-slate-500">Loading threat intelligence...</p> : query.isError || !data ? <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">Unable to load threat intelligence.</p> : (
            <div className="grid gap-6 xl:grid-cols-2">
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><Globe2 className="size-5 text-cyan-600" />Observed source indicators</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {data.top_threat_sources.map((source, index) => (
                    <article key={source.source_ip} className="grid grid-cols-[36px_1fr_auto] items-center gap-3 rounded-xl border p-4">
                      <span className="flex size-9 items-center justify-center rounded-lg bg-slate-100 text-sm font-semibold">{index + 1}</span>
                      <div><p className="font-mono text-sm font-semibold">{source.source_ip}</p><p className="mt-1 text-xs text-slate-500">Seen in {source.count} event{source.count === 1 ? "" : "s"}</p></div>
                      <Badge variant="outline" className="border-red-200 bg-red-50 text-red-700">Risk {source.max_risk_score.toFixed(0)}</Badge>
                    </article>
                  ))}
                  {!data.top_threat_sources.length && <p className="text-sm text-slate-500">No source indicators observed.</p>}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><Crosshair className="size-5 text-violet-600" />Attack techniques</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {data.top_attack_types.map((attack) => {
                    const technique = techniques[attack.name.toUpperCase()] ?? { id: "—", name: "Unmapped observed behavior" };
                    return <article key={attack.name} className="rounded-xl border p-4"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold">{attack.name}</p><p className="mt-1 text-sm text-slate-500">{technique.id} · {technique.name}</p></div><Badge>{attack.count} events</Badge></div></article>;
                  })}
                  {!data.top_attack_types.length && <p className="text-sm text-slate-500">No attack patterns observed.</p>}
                </CardContent>
              </Card>
              <Card className="xl:col-span-2"><CardContent className="flex items-start gap-4 p-5"><ShieldAlert className="mt-0.5 size-5 text-amber-600" /><div><p className="font-medium">Operational scope</p><p className="mt-1 text-sm leading-6 text-slate-500">This view reflects locally observed detections and curated ATT&amp;CK mappings. It does not claim external reputation or enrichment data.</p></div></CardContent></Card>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

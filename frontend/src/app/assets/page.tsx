"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Globe2, Monitor, RefreshCw, Search } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getAssetOverview } from "@/lib/api/soc";

export default function AssetsPage() {
  const { t } = useLanguage();
  const [search, setSearch] = useState("");
  const query = useQuery({ queryKey: ["asset-overview", search], queryFn: () => getAssetOverview(search) });
  return <div className="flex min-h-screen bg-slate-50 text-slate-950"><Sidebar /><div className="min-w-0 flex-1"><Topbar /><main className="mx-auto max-w-[1500px] p-5 md:p-8">
    <header className="mb-8 flex items-end justify-between gap-4"><div><p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">{t("Protected inventory")}</p><h1 className="text-3xl font-semibold">{t("Assets")}</h1><p className="mt-2 text-sm text-slate-500">{t("Systems observed by CyberSentinel with authorized detection and active-incident counts.")}</p></div><Button variant="outline" onClick={() => query.refetch()} disabled={query.isFetching}><RefreshCw className={query.isFetching ? "animate-spin" : ""} />{t("Refresh")}</Button></header>
    <div className="relative mb-5 max-w-md"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><Input className="pl-10" value={search} onChange={(event) => setSearch(event.target.value)} placeholder={t("Search hostname, IP or asset ID...")} /></div>
    {query.isLoading ? <p className="py-16 text-center text-slate-500">{t("Loading assets...")}</p> : query.isError ? <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">{t("Assets could not be loaded. Try again.")}</p> : !query.data?.length ? <p className="rounded-xl border bg-white p-12 text-center text-slate-500">{t("No assets match this search.")}</p> : <section className="grid gap-4 lg:grid-cols-2">{query.data.map((asset) => <Card key={asset.id}><CardContent className="space-y-4 p-5"><div className="flex items-start justify-between gap-3"><div className="flex gap-3"><span className="flex size-10 items-center justify-center rounded-xl bg-cyan-50"><Monitor className="size-5 text-cyan-700" /></span><div><h2 className="font-semibold">{asset.hostname}</h2><p className="font-mono text-xs text-slate-500">{asset.id} · {asset.primary_ip ?? t("No IP")}</p></div></div><Badge variant="outline">{asset.status}</Badge></div><div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4"><div><p className="text-xs text-slate-400">{t("Environment")}</p><p>{asset.environment}</p></div><div><p className="text-xs text-slate-400">{t("Criticality")}</p><p>{asset.criticality}</p></div><div><p className="text-xs text-slate-400">{t("Detections")}</p><p className="font-semibold">{asset.detections_count}</p></div><div><p className="text-xs text-slate-400">{t("Active incidents")}</p><p className="font-semibold">{asset.active_incidents_count}</p></div></div><div className="flex flex-wrap items-center gap-2 text-xs text-slate-500"><span>{asset.operating_system ?? t("Unknown OS")}</span><span>·</span><span>{asset.owner_team ?? t("Unassigned")}</span>{asset.internet_facing && <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-800"><Globe2 />{t("Internet-facing")}</Badge>}<span className="ml-auto">{t("Last seen")}: {asset.last_seen_at ? new Date(asset.last_seen_at).toLocaleString() : t("Unknown")}</span></div></CardContent></Card>)}</section>}
  </main></div></div>;
}

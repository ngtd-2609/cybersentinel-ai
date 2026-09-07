"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, BrainCircuit, CheckCircle2, Database, GitCommit, RefreshCw, ShieldCheck } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getModelEvaluationEvidence } from "@/lib/api/mlops";

const percent = (value: number, digits = 2) => `${(value * 100).toFixed(digits)}%`;

export default function ModelsPage() {
  const { t } = useLanguage();
  const query = useQuery({
    queryKey: ["model-evaluation-evidence"],
    queryFn: getModelEvaluationEvidence,
    staleTime: 30 * 60_000,
  });
  const evidence = query.data;
  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-6xl p-5 md:p-8">
          <header className="mb-8">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700"><BrainCircuit className="size-4" />MLOps evidence</div>
            <h1 className="text-3xl font-semibold">{t("Model Monitor")}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">Canonical locked-test evidence for the released portfolio classifier. Runtime service health is reported separately in System Monitoring.</p>
          </header>
          {query.isLoading ? <p className="py-16 text-center text-slate-500">Loading model evidence...</p> : query.isError || !evidence ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-800"><p>Model evidence is unavailable. No evaluation result can be confirmed right now.</p><Button className="mt-3" variant="outline" onClick={() => query.refetch()}><RefreshCw />Retry</Button></div>
          ) : (
            <section className="space-y-5">
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between gap-3"><div className="flex size-11 items-center justify-center rounded-xl bg-cyan-50"><ShieldCheck className="size-5 text-cyan-700" /></div><Badge className={evidence.quality_gate_passed ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-800"}>{evidence.quality_gate_passed ? <CheckCircle2 /> : <AlertTriangle />}{evidence.quality_gate_passed ? "Release gate passed" : "Release gate not passed"}</Badge></div>
                  <CardTitle className="mt-3">{evidence.model_name}</CardTitle><p className="text-sm text-slate-500">{evidence.task} · version {evidence.model_version}</p>
                </CardHeader>
                <CardContent className="space-y-5">
                  <div className="grid grid-cols-2 gap-2 text-center text-xs md:grid-cols-3 xl:grid-cols-6">
                    {[["Precision", percent(evidence.metrics.precision, 4)], ["Recall", percent(evidence.metrics.recall, 4)], ["F1", percent(evidence.metrics.f1, 4)], ["FPR", percent(evidence.metrics.false_positive_rate, 6)], ["ROC-AUC", evidence.metrics.roc_auc.toFixed(6)], ["PR-AUC", evidence.metrics.pr_auc.toFixed(6)]].map(([label, value]) => <div key={label} className="rounded-lg bg-slate-50 p-3"><p className="text-slate-500">{label}</p><p className="mt-1 font-semibold text-slate-900">{value}</p></div>)}
                  </div>
                  <div className="grid gap-3 text-xs text-slate-600 md:grid-cols-2">
                    <p className="flex items-start gap-2"><Database className="mt-0.5 size-4 shrink-0" /><span><strong>Dataset:</strong> {evidence.dataset_name}<br /><strong>Split:</strong> {evidence.split}</span></p>
                    <p className="flex items-start gap-2"><GitCommit className="mt-0.5 size-4 shrink-0" /><span><strong>Evaluation:</strong> {evidence.evaluation}<br /><strong>Threshold:</strong> {evidence.selected_threshold} · <strong>Evidence:</strong> {evidence.source}</span></p>
                  </div>
                </CardContent>
              </Card>
              <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-950"><strong>Interpretation:</strong> this locked temporal test has very high precision and a low false-positive rate, but recall drops under temporal shift. The classifier is one signal in the detection pipeline—not the only detection engine.</p>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}

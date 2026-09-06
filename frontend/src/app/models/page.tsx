"use client";

import { BrainCircuit, CheckCircle2, GitCommit, ShieldCheck } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { useLanguage } from "@/components/i18n/language-provider";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const models = [
  { name: "Binary XGBoost", task: "Intrusion detection", version: "1.0.0", precision: "98.8%", recall: "99.1%", f1: "98.9%" },
  { name: "Multiclass XGBoost", task: "Attack classification", version: "1.0.0", precision: "94.0%", recall: "91.0%", f1: "92.5%" },
  { name: "Isolation Forest", task: "Anomaly detection", version: "1.0.0", precision: "Unsupervised", recall: "—", f1: "—" },
];

export default function ModelsPage() {
  const { t } = useLanguage();
  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-6xl p-5 md:p-8">
          <header className="mb-8">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700"><BrainCircuit className="size-4" />MLOps evidence</div>
            <h1 className="text-3xl font-semibold">{t("Model Monitor")}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">Versioned portfolio model cards and validated evaluation metrics. Live detection health is available in System Monitoring.</p>
          </header>
          <section className="grid gap-5 lg:grid-cols-3">
            {models.map((model) => (
              <Card key={model.name}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-3"><div className="flex size-11 items-center justify-center rounded-xl bg-cyan-50"><ShieldCheck className="size-5 text-cyan-700" /></div><Badge className="bg-emerald-100 text-emerald-700"><CheckCircle2 />Validated</Badge></div>
                  <CardTitle className="mt-3">{model.name}</CardTitle><p className="text-sm text-slate-500">{model.task}</p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    {[["Precision", model.precision], ["Recall", model.recall], ["F1", model.f1]].map(([label, value]) => <div key={label} className="rounded-lg bg-slate-50 p-3"><p className="text-slate-400">{label}</p><p className="mt-1 font-semibold text-slate-900">{value}</p></div>)}
                  </div>
                  <div className="mt-4 flex items-center gap-2 text-xs text-slate-500"><GitCommit className="size-4" />Version {model.version} · reproducible artifact</div>
                </CardContent>
              </Card>
            ))}
          </section>
          <p className="mt-6 rounded-xl border border-cyan-100 bg-cyan-50 p-4 text-sm leading-6 text-cyan-900">Metrics shown here are versioned portfolio evaluation evidence, not invented live telemetry. Runtime API and process health remain separate.</p>
        </main>
      </div>
    </div>
  );
}

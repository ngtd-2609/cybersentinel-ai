"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Bot, BookOpen, Send, Sparkles } from "lucide-react";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { askCopilot } from "@/lib/api/incidents";

const prompts = [
  "How should I investigate a ransomware detection?",
  "Give me a containment checklist for SSH brute force.",
  "What evidence should I preserve during malware triage?",
];

export default function CopilotPage() {
  const [question, setQuestion] = useState(prompts[0]);
  const [context, setContext] = useState("");
  const mutation = useMutation({
    mutationFn: () => askCopilot(question.trim(), context.trim()),
  });

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-950">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Topbar />
        <main className="mx-auto max-w-6xl p-5 md:p-8">
          <header className="mb-8">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-violet-700"><Sparkles className="size-4" />Grounded investigation assistant</div>
            <h1 className="text-3xl font-semibold tracking-tight">SOC Copilot</h1>
            <p className="mt-2 text-sm text-slate-500">Ask operational security questions backed by the local CyberSentinel knowledge base.</p>
          </header>

          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_340px]">
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Bot className="size-5 text-violet-600" />Investigation question</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <Textarea rows={4} value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about a detection, incident or response procedure..." />
                <Textarea rows={5} value={context} onChange={(event) => setContext(event.target.value)} placeholder="Optional alert context: IP addresses, attack label, risk score, observations..." />
                <Button disabled={!question.trim() || mutation.isPending} onClick={() => mutation.mutate()}>
                  <Send />{mutation.isPending ? "Analyzing..." : "Ask Copilot"}
                </Button>
                {mutation.isError && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{mutation.error.message}</p>}
                {mutation.data && (
                  <section className="space-y-5 border-t pt-5">
                    <div className="flex items-center justify-between"><h2 className="font-semibold">Analysis</h2><Badge variant="outline">{mutation.data.model}</Badge></div>
                    <p className="whitespace-pre-wrap text-sm leading-7 text-slate-700">{mutation.data.answer}</p>
                    <div>
                      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold"><BookOpen className="size-4" />Knowledge sources</h3>
                      <div className="grid gap-3 sm:grid-cols-2">
                        {mutation.data.sources.map((source) => (
                          <article key={source.document_id} className="rounded-xl border bg-slate-50 p-4 text-sm">
                            <p className="font-medium">{source.title}</p>
                            <p className="mt-1 text-xs text-slate-500">{source.source}</p>
                            <p className="mt-2 text-xs font-semibold text-cyan-700">Relevance {(source.score * 100).toFixed(0)}%</p>
                          </article>
                        ))}
                      </div>
                    </div>
                  </section>
                )}
              </CardContent>
            </Card>

            <aside className="space-y-4">
              <Card>
                <CardHeader><CardTitle className="text-base">Suggested questions</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  {prompts.map((prompt) => <Button key={prompt} variant="outline" className="h-auto w-full justify-start whitespace-normal py-3 text-left" onClick={() => setQuestion(prompt)}>{prompt}</Button>)}
                </CardContent>
              </Card>
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-800">Copilot recommendations support analyst decisions. Validate commands and evidence before taking action.</div>
            </aside>
          </div>
        </main>
      </div>
    </div>
  );
}

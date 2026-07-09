import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { PromptInput } from "@/components/create-flow/prompt-input";
import { CreateOptionsPanel } from "@/components/create-flow/create-options";
import { GrillPanel } from "@/components/create-flow/grill-panel";
import { StagedChecklist } from "@/components/create-flow/staged-checklist";
import { DEFAULT_OPTIONS, CREATE_STAGES } from "@/contracts/create";
import type { CreateOptions, GrillResult } from "@/contracts/create";
import { Sparkles, Send, RotateCcw } from "lucide-react";

type StageStatus = "pending" | "active" | "completed" | "failed";

export function CreatePage() {
  const [prompt, setPrompt] = useState("");
  const [options, setOptions] = useState<CreateOptions>(DEFAULT_OPTIONS);
  const [grillResult, setGrillResult] = useState<GrillResult | null>(null);
  const [grillLoading, setGrillLoading] = useState(false);
  const [stages, setStages] = useState(CREATE_STAGES.map(s => ({ ...s, status: "pending" as StageStatus })));

  const handleGrill = useCallback(async () => {
    if (prompt.trim().length < 10) return;
    setGrillLoading(true);
    setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "active" as StageStatus } : s));
    try {
      await new Promise(r => setTimeout(r, 1500));
      setGrillResult({
        refinedPrompt: `Create detailed technical explainer video about: ${prompt}. Include animated diagrams, code walkthrough, and key architectural insights.`,
        suggestedScenes: [
          { kind: "title", title: "Introduction", description: `Overview of ${prompt}`, reasoning: "Standard opener" },
          { kind: "bullets", title: "Key Concepts", description: "Core ideas explained simply", reasoning: "Break down topic" },
          { kind: "code", title: "Code Walkthrough", description: "Step-by-step implementation", reasoning: "Visual code explanation" },
          { kind: "diagram", title: "Architecture", description: "System diagram", reasoning: "Visual understanding" },
          { kind: "outro", title: "Summary", description: "Recap and next steps", reasoning: "Closing" },
        ],
        missingDetails: [],
        confidence: 0.85,
      });
      setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "completed" as StageStatus } : s));
    } catch {
      setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "failed" as StageStatus } : s));
    } finally {
      setGrillLoading(false);
    }
  }, [prompt]);

  const handleReset = useCallback(() => {
    setPrompt(""); setGrillResult(null); setGrillLoading(false);
    setStages(CREATE_STAGES.map(s => ({ ...s, status: "pending" as StageStatus })));
  }, []);

  const canGrill = prompt.trim().length >= 10 && !grillLoading;

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Create video</h1>
        <p className="text-sm text-muted-foreground">Describe your video — we handle the rest</p>
      </div>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base"><Sparkles className="h-4 w-4 text-primary" />What do you want to create?</CardTitle>
              <CardDescription>Describe topic, style, and key points for your video</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <PromptInput value={prompt} onChange={setPrompt} disabled={grillLoading} />
              <CreateOptionsPanel options={options} onChange={setOptions} disabled={grillLoading} />
              <div className="flex gap-2 pt-2">
                <Button onClick={handleGrill} disabled={!canGrill}><Send className="mr-2 h-4 w-4" />{grillLoading ? "Grilling..." : "Grill prompt"}</Button>
                <Button variant="ghost" size="icon" onClick={handleReset} disabled={grillLoading}><RotateCcw className="h-4 w-4" /></Button>
              </div>
            </CardContent>
          </Card>
          <GrillPanel result={grillResult} loading={grillLoading} />
          {grillResult && !grillLoading && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Director preview</CardTitle>
                <CardDescription>{grillResult.suggestedScenes.length} scenes planned</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 sm:grid-cols-2">
                  {grillResult.suggestedScenes.map((scene, i) => (
                    <div key={i} className="space-y-1.5 rounded-lg border bg-secondary/20 p-3">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="font-mono">#{i + 1}</span>
                        <span className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider">{scene.kind}</span>
                      </div>
                      <p className="text-sm font-medium">{scene.title}</p>
                      <p className="text-xs text-muted-foreground">{scene.description}</p>
                    </div>
                  ))}
                </div>
                <Separator className="my-4" />
                <div className="flex justify-end"><Button size="lg" disabled>Start job</Button></div>
              </CardContent>
            </Card>
          )}
        </div>
        <div className="lg:col-span-1">
          <Card className="sticky top-8">
            <CardHeader><CardTitle className="text-base">Progress</CardTitle><CardDescription>Pipeline stage tracker</CardDescription></CardHeader>
            <CardContent><StagedChecklist stages={stages} /></CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

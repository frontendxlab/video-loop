import { useState, useCallback } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { PromptInput } from "@/components/create-flow/prompt-input";
import { CreateOptionsPanel } from "@/components/create-flow/create-options";
import { GrillPanel } from "@/components/create-flow/grill-panel";
import { RecipePicker } from "@/components/create-flow/recipe-picker";
import { StagedChecklist } from "@/components/create-flow/staged-checklist";
import { DEFAULT_OPTIONS, CREATE_STAGES } from "@/contracts/create";
import type { CreateOptions, GrillResult, Recipe } from "@/contracts/create";
import { grillPrompt, createJob } from "@/api/jobs";
import { Sparkles, Send, RotateCcw, Loader2 } from "lucide-react";

type StageStatus = "pending" | "active" | "completed" | "failed";

export function CreatePage() {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState("");
  const [options, setOptions] = useState<CreateOptions>(DEFAULT_OPTIONS);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [grillResult, setGrillResult] = useState<GrillResult | null>(null);
  const [grillLoading, setGrillLoading] = useState(false);
  const [jobLoading, setJobLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stages, setStages] = useState(CREATE_STAGES.map(s => ({ ...s, status: "pending" as StageStatus })));

  const handleGrill = useCallback(async () => {
    if (prompt.trim().length < 10) return;
    setError(null);
    setGrillLoading(true);
    setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "active" as StageStatus } : s));
    try {
      const result = await grillPrompt(prompt, options);
      setGrillResult(result);
      setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "completed" as StageStatus } : s));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Grill failed";
      setError(msg);
      setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "failed" as StageStatus } : s));
    } finally {
      setGrillLoading(false);
    }
  }, [prompt, options]);

  const handleCreateJob = useCallback(async () => {
    if (!grillResult) return;
    setError(null);
    setJobLoading(true);
    setStages(prev => prev.map(s => s.id === "plan" ? { ...s, status: "active" as StageStatus } : s));
    try {
      const resp = await createJob(prompt, options, selectedRecipe?.id);
      navigate({ to: "/jobs/$jobId", params: { jobId: resp.jobId } });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Job creation failed";
      setError(msg);
      setStages(prev => prev.map(s => s.id === "plan" ? { ...s, status: "failed" as StageStatus } : s));
    } finally {
      setJobLoading(false);
    }
  }, [grillResult, prompt, options, navigate]);

  const handleReset = useCallback(() => {
    setPrompt(""); setSelectedRecipe(null); setGrillResult(null); setGrillLoading(false); setJobLoading(false); setError(null);
    setStages(CREATE_STAGES.map(s => ({ ...s, status: "pending" as StageStatus })));
  }, []);

  const canGrill = prompt.trim().length >= 10 && !grillLoading && !jobLoading;

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Create video</h1>
        <p className="text-sm text-muted-foreground">Describe your video — we handle the rest</p>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base"><Sparkles className="h-4 w-4 text-primary" />What do you want to create?</CardTitle>
              <CardDescription>Describe topic, style, and key points for your video</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <PromptInput value={prompt} onChange={setPrompt} disabled={grillLoading || jobLoading} />
              <RecipePicker selected={selectedRecipe} onSelect={setSelectedRecipe} disabled={grillLoading || jobLoading} />
              <CreateOptionsPanel options={options} onChange={setOptions} disabled={grillLoading || jobLoading} />
              <div className="flex gap-2 pt-2">
                <Button onClick={handleGrill} disabled={!canGrill}>
                  {grillLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Grilling...</> : <><Send className="mr-2 h-4 w-4" />Grill prompt</>}
                </Button>
                <Button variant="ghost" size="icon" onClick={handleReset} disabled={grillLoading || jobLoading}><RotateCcw className="h-4 w-4" /></Button>
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
                <div className="flex justify-end">
                  <Button size="lg" onClick={handleCreateJob} disabled={jobLoading}>
                    {jobLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Starting...</> : "Start job"}
                  </Button>
                </div>
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

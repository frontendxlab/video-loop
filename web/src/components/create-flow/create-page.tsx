import { useState, useCallback } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { PromptInput } from "@/components/create-flow/prompt-input";
import { CreateOptionsPanel } from "@/components/create-flow/create-options";
import { GrillPanel } from "@/components/create-flow/grill-panel";
import { RecipePicker } from "@/components/create-flow/recipe-picker";
import { TemplatePicker } from "@/components/create-flow/template-picker";
import { StagedChecklist } from "@/components/create-flow/staged-checklist";
import { DEFAULT_OPTIONS, CREATE_STAGES } from "@/contracts/create";
import type { CreateOptions, GrillResult, Recipe, SuggestedTemplate } from "@/contracts/create";
import { startGrill, submitGrillTurn, createJob } from "@/api/jobs";
import { Sparkles, RotateCcw, Loader2 } from "lucide-react";

type StageStatus = "pending" | "active" | "completed" | "failed";
type GrillPhase = "idle" | "conversation" | "complete";

type Message = {
  role: "assistant" | "user";
  text: string;
};

export function CreatePage() {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState("");
  const [options, setOptions] = useState<CreateOptions>(DEFAULT_OPTIONS);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [selectedTemplates, setSelectedTemplates] = useState<string[]>([]);
  const [grillResult, setGrillResult] = useState<GrillResult | null>(null);
  const [grillPhase, setGrillPhase] = useState<GrillPhase>("idle");
  const [grillLoading, setGrillLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string>("");
  const [jobLoading, setJobLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stages, setStages] = useState(CREATE_STAGES.map(s => ({ ...s, status: "pending" as StageStatus })));

  const handleGrill = useCallback(async () => {
    if (prompt.trim().length < 10) return;
    setError(null);
    setGrillLoading(true);
    setGrillPhase("conversation");
    setMessages([]);
    setCurrentQuestion("");
    setGrillResult(null);
    setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "active" as StageStatus } : s));
    try {
      const start = await startGrill(prompt, options);
      setSessionId(start.sessionId);
      if (start.question) {
        setCurrentQuestion(start.question);
        setMessages([{ role: "assistant", text: start.question }]);
      } else {
        // No questions needed — immediate result
        handleFinishGrill(start.sessionId);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Grill failed";
      setError(msg);
      setGrillPhase("idle");
      setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "failed" as StageStatus } : s));
    } finally {
      setGrillLoading(false);
    }
  }, [prompt, options]);

  const handleSendAnswer = useCallback(async (answer: string, done: boolean) => {
    if (!sessionId) return;
    setGrillLoading(true);
    setMessages(prev => [...prev, { role: "user", text: answer }]);
    setCurrentQuestion("");
    try {
      const turn = await submitGrillTurn(sessionId, answer, done);
      if (turn.done && turn.result) {
        setGrillResult(turn.result);
        setGrillPhase("complete");
        setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "completed" as StageStatus } : s));
        setMessages(prev => [...prev, { role: "assistant", text: "Great! I have enough details to create your video." }]);
      } else if (turn.question) {
        setCurrentQuestion(turn.question);
        setMessages(prev => [...prev, { role: "assistant", text: turn.question! }]);
      } else {
        // Shouldn't happen — treat as done
        setGrillPhase("complete");
        setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "completed" as StageStatus } : s));
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Grill turn failed";
      setError(msg);
    } finally {
      setGrillLoading(false);
    }
  }, [sessionId]);

  const handleFinishGrill = useCallback(async (sid?: string) => {
    const id = sid ?? sessionId;
    if (!id) return;
    setGrillLoading(true);
    try {
      const turn = await submitGrillTurn(id, "done", true);
      if (turn.result) {
        setGrillResult(turn.result);
        setGrillPhase("complete");
        setStages(prev => prev.map(s => s.id === "grill" ? { ...s, status: "completed" as StageStatus } : s));
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to finalize grill";
      setError(msg);
    } finally {
      setGrillLoading(false);
    }
  }, [sessionId]);

  const handleCreateJob = useCallback(async () => {
    if (!grillResult) return;
    setError(null);
    setJobLoading(true);
    setStages(prev => prev.map(s => s.id === "plan" ? { ...s, status: "active" as StageStatus } : s));
    try {
      const resp = await createJob(prompt, options, selectedRecipe?.id, selectedTemplates, sessionId ?? undefined);
      navigate({ to: "/jobs/$jobId", params: { jobId: resp.jobId } });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Job creation failed";
      setError(msg);
      setStages(prev => prev.map(s => s.id === "plan" ? { ...s, status: "failed" as StageStatus } : s));
    } finally {
      setJobLoading(false);
    }
  }, [grillResult, prompt, options, selectedRecipe, navigate, sessionId]);

  const handleReset = useCallback(() => {
    setPrompt(""); setSelectedRecipe(null); setSelectedTemplates([]); setGrillResult(null); setGrillLoading(false); setJobLoading(false); setError(null);
    setGrillPhase("idle"); setSessionId(null); setMessages([]); setCurrentQuestion("");
    setStages(CREATE_STAGES.map(s => ({ ...s, status: "pending" as StageStatus })));
  }, []);

  const canGrill = prompt.trim().length >= 10 && !grillLoading && !jobLoading && grillPhase === "idle";

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
              <TemplatePicker
                selected={selectedTemplates}
                onSelect={setSelectedTemplates}
                suggestions={grillResult?.suggestedTemplates ?? []}
                disabled={grillLoading || jobLoading}
              />
              <RecipePicker selected={selectedRecipe} onSelect={setSelectedRecipe} disabled={grillLoading || jobLoading} />
              <CreateOptionsPanel options={options} onChange={setOptions} disabled={grillLoading || jobLoading} />
              <div className="flex gap-2 pt-2">
                <Button onClick={handleGrill} disabled={!canGrill}>
                  {grillLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Grilling...</> : <><Sparkles className="mr-2 h-4 w-4" />Grill me</>}
                </Button>
                <Button variant="ghost" size="icon" onClick={handleReset} disabled={grillLoading || jobLoading}><RotateCcw className="h-4 w-4" /></Button>
              </div>
            </CardContent>
          </Card>

          <GrillPanel
            result={grillResult}
            loading={grillLoading}
            conversationMode={grillPhase === "conversation"}
            messages={messages}
            currentQuestion={currentQuestion}
            onSendAnswer={handleSendAnswer}
          />

          {grillResult && grillPhase === "complete" && (
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
                {grillResult.suggestedTemplates.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <h4 className="text-xs font-medium text-muted-foreground">Suggested templates ({grillResult.suggestedTemplates.length})</h4>
                    <div className="flex flex-wrap gap-2">
                      {grillResult.suggestedTemplates.map((t) => (
                        <div key={t.id} className="rounded-md border bg-secondary/10 px-2.5 py-1.5 text-xs">
                          <span className="font-medium">{t.name}</span>
                          <span className="ml-1 text-muted-foreground">({t.scene_count} scenes)</span>
                          <p className="mt-0.5 text-[10px] text-muted-foreground/70">{t.match_reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
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

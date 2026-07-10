import { useState, useRef, useEffect } from "react";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { GrillResult } from "@/contracts/create";
import { Send, Check, Loader2 } from "lucide-react";

type Message = {
  role: "assistant" | "user";
  text: string;
};

interface GrillPanelProps {
  result: GrillResult | null;
  loading: boolean;
  className?: string;
  /** Multi-turn conversation mode */
  conversationMode?: boolean;
  messages?: Message[];
  currentQuestion?: string;
  onSendAnswer?: (answer: string, done: boolean) => void;
}

export function GrillPanel({
  result, loading, className,
  conversationMode, messages, currentQuestion, onSendAnswer,
}: GrillPanelProps) {
  const [answer, setAnswer] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (conversationMode && inputRef.current) {
      inputRef.current.focus();
    }
  }, [currentQuestion, conversationMode]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const trimmed = answer.trim();
    if (!trimmed || !onSendAnswer) return;
    onSendAnswer(trimmed, false);
    setAnswer("");
  };

  const handleDone = () => {
    const trimmed = answer.trim();
    if (onSendAnswer) {
      onSendAnswer(trimmed || "done", true);
    }
    setAnswer("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Conversation mode — show chat UI
  if (conversationMode) {
    return (
      <Card className={cn("", className)}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Grill panel</CardTitle>
            {loading && <div className="flex items-center gap-2"><Progress value={0} className="h-1.5 w-20" /><span className="text-xs text-muted-foreground">Thinking...</span></div>}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="max-h-64 space-y-3 overflow-y-auto rounded-md border bg-secondary/10 p-3">
            {messages?.map((msg, i) => (
              <div key={i} className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
                <div className={cn(
                  "max-w-[80%] rounded-lg px-3 py-2 text-sm",
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground",
                )}>
                  {msg.text}
                </div>
              </div>
            ))}
            {currentQuestion && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg bg-secondary px-3 py-2 text-sm text-secondary-foreground">
                  {currentQuestion}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {loading && (
            <div className="flex items-center justify-center gap-2 py-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Processing...
            </div>
          )}

          {!loading && (
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your answer..."
                className="flex-1"
              />
              <Button size="sm" onClick={handleSend} disabled={!answer.trim()}>
                <Send className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="outline" onClick={handleDone}>
                <Check className="h-4 w-4" /><span className="ml-1">Done</span>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Result mode — show grilled result (original behavior)
  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Grill panel</CardTitle>
          {loading && <div className="flex items-center gap-2"><Progress value={0} className="h-1.5 w-20" /><span className="text-xs text-muted-foreground">Grilling...</span></div>}
          {result && <Badge variant={result.confidence > 0.7 ? "success" : "warning"}>{Math.round(result.confidence * 100)}% confidence</Badge>}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading && <div className="space-y-3 p-2"><div className="h-3 w-full animate-pulse rounded bg-secondary" /><div className="h-3 w-3/4 animate-pulse rounded bg-secondary" /><div className="h-3 w-5/6 animate-pulse rounded bg-secondary" /></div>}
        {!loading && !result && <p className="py-4 text-center text-sm text-muted-foreground">Submit a prompt to see grill results</p>}
        {result && !loading && <>
          <div className="space-y-1">
            <span className="text-xs font-medium text-muted-foreground">Refined prompt</span>
            <p className="rounded-md bg-secondary/50 p-3 text-sm leading-relaxed">{result.refinedPrompt}</p>
          </div>
          <Accordion type="multiple">
            <AccordionItem value="scenes">
              <AccordionTrigger>Suggested scenes ({result.suggestedScenes.length})</AccordionTrigger>
              <AccordionContent className="space-y-2">
                {result.suggestedScenes.map((scene, i) => (
                  <div key={i} className="space-y-1 rounded-md border p-3">
                    <div className="flex items-center gap-2"><Badge variant="outline" className="text-[10px]">{scene.kind}</Badge><span className="text-sm font-medium">{scene.title}</span></div>
                    <p className="text-xs text-muted-foreground">{scene.description}</p>
                    <p className="text-[11px] italic text-muted-foreground/70">{scene.reasoning}</p>
                  </div>
                ))}
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="missing">
              <AccordionTrigger>Missing details ({result.missingDetails.length})</AccordionTrigger>
              <AccordionContent>
                {result.missingDetails.length === 0
                  ? <p className="text-xs text-muted-foreground">No missing details</p>
                  : <ul className="list-inside list-disc space-y-1">{result.missingDetails.map((d, i) => <li key={i} className="text-xs text-muted-foreground">{d}</li>)}</ul>
                }
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </>}
      </CardContent>
    </Card>
  );
}

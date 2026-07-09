import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { GrillResult } from "@/contracts/create";

interface GrillPanelProps {
  result: GrillResult | null;
  loading: boolean;
  className?: string;
}

export function GrillPanel({ result, loading, className }: GrillPanelProps) {
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

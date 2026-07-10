import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { GENRE_TEMPLATES } from "@/contracts/create";
import type { VideoTemplate, SuggestedTemplate } from "@/contracts/create";
import { Lightbulb, BookOpen, Monitor, Megaphone, ScrollText, BarChart3, GitCompare, Clock, Star } from "lucide-react";

interface TemplatePickerProps {
  selected: string[];
  onSelect: (ids: string[]) => void;
  suggestions: SuggestedTemplate[];
  disabled?: boolean;
  className?: string;
}

const iconMap: Record<string, React.ReactNode> = {
  lightbulb: <Lightbulb className="h-4 w-4" />,
  "book-open": <BookOpen className="h-4 w-4" />,
  monitor: <Monitor className="h-4 w-4" />,
  megaphone: <Megaphone className="h-4 w-4" />,
  "scroll-text": <ScrollText className="h-4 w-4" />,
  "bar-chart-3": <BarChart3 className="h-4 w-4" />,
  "git-compare": <GitCompare className="h-4 w-4" />,
  clock: <Clock className="h-4 w-4" />,
  star: <Star className="h-4 w-4" />,
};

export function TemplatePicker({ selected, onSelect, suggestions, disabled, className }: TemplatePickerProps) {
  const templateMap = new Map(GENRE_TEMPLATES.map(t => [t.id, t]));
  const suggestionIds = new Set(suggestions.map(s => s.id));

  const toggle = (id: string) => {
    if (disabled) return;
    onSelect(selected.includes(id) ? selected.filter(s => s !== id) : [...selected, id]);
  };

  const displayTemplates = suggestions.length > 0
    ? GENRE_TEMPLATES.filter(t => suggestionIds.has(t.id))
    : GENRE_TEMPLATES;

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm">Templates</CardTitle>
            <CardDescription>
              {selected.length > 0
                ? `${selected.length} selected — shapes scene structure`
                : "Pick video genre templates to guide scene planning"}
            </CardDescription>
          </div>
          {selected.length > 0 && (
            <Badge variant="secondary" className="text-xs">{selected.length} selected</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        <ScrollArea className="max-h-[400px] pr-2">
          <TooltipProvider>
          <div className="space-y-2">
            {displayTemplates.map((template) => {
              const isSelected = selected.includes(template.id);
              const suggestion = suggestions.find(s => s.id === template.id);
              return (
                <button
                  key={template.id}
                  onClick={() => toggle(template.id)}
                  disabled={disabled}
                  className={cn(
                    "w-full rounded-md border px-3 py-2.5 text-left transition-colors hover:bg-secondary/50",
                    isSelected ? "border-primary ring-1 ring-primary" : "border-border",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className="shrink-0 text-muted-foreground">
                        {iconMap[template.icon] ?? <Lightbulb className="h-4 w-4" />}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm font-medium">{template.name}</span>
                          <Badge variant="outline" className="text-[10px]">{template.category}</Badge>
                        </div>
                        <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                          {template.description}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Scene preview */}
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {template.scenes.map((scene, i) => (
                      <Tooltip key={i}>
                        <TooltipTrigger asChild>
                          <span className="rounded bg-secondary/40 px-1.5 py-0.5 text-[10px] text-muted-foreground cursor-default">
                            {i + 1}. {scene.sceneType}
                          </span>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" className="text-xs">
                          {scene.title}: {scene.description}
                        </TooltipContent>
                      </Tooltip>
                    ))}
                  </div>

                  {/* Match reason from grill */}
                  {suggestion && (
                    <p className="mt-1 text-[10px] italic text-primary/60">
                      {suggestion.match_reason}
                    </p>
                  )}
                </button>
              );
            })}
          </div>
          </TooltipProvider>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

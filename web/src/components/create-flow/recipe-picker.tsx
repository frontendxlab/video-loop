import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { RECIPE_PRESETS } from "@/contracts/create";
import type { Recipe } from "@/contracts/create";

interface RecipePickerProps {
  selected: Recipe | null;
  onSelect: (recipe: Recipe | null) => void;
  disabled?: boolean;
  className?: string;
}

const engineColors: Record<string, string> = {
  remotion: "bg-blue-500/10 text-blue-600 border-blue-200 dark:border-blue-800",
  manim: "bg-purple-500/10 text-purple-600 border-purple-200 dark:border-purple-800",
  animotion: "bg-amber-500/10 text-amber-600 border-amber-200 dark:border-amber-800",
};

const badgeVariantMap: Record<string, "default" | "secondary" | "outline" | "success" | "warning" | undefined> = {
  default: "default",
  secondary: "secondary",
  outline: "outline",
  success: "success",
  warning: "warning",
};

export function RecipePicker({ selected, onSelect, disabled, className }: RecipePickerProps) {
  const [showAll, setShowAll] = useState(false);

  const handleToggle = useCallback(() => {
    if (!disabled) setShowAll((p) => !p);
  }, [disabled]);

  const handleSelect = useCallback(
    (recipe: Recipe) => {
      if (disabled) return;
      if (selected?.id === recipe.id) {
        onSelect(null);
      } else {
        onSelect(recipe);
      }
    },
    [disabled, selected, onSelect],
  );

  return (
    <Card className={cn("", className)}>
      <CardHeader className="cursor-pointer select-none" onClick={handleToggle}>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm">Recipe</CardTitle>
            <CardDescription>
              {selected
                ? `${selected.name} — carried into job`
                : showAll
                  ? "Pick a recipe template"
                  : "Pick a recipe to guide scene structure"}
            </CardDescription>
          </div>
          {selected && (
            <Badge
              variant="outline"
              className={cn("text-xs", engineColors[selected.preferredEngine] ?? "bg-secondary/50")}
            >
              {selected.name}
            </Badge>
          )}
        </div>
      </CardHeader>
      {showAll && (
        <CardContent className="space-y-2 pt-0">
          <button
            onClick={() => onSelect(null)}
            className={cn(
              "w-full rounded-md border px-3 py-2 text-left text-xs transition-colors hover:bg-secondary/50",
              !selected ? "border-primary ring-1 ring-primary" : "border-border",
            )}
            disabled={disabled}
          >
            <span className="font-medium">No recipe</span>
            <span className="ml-2 text-muted-foreground">— free-form prompt only</span>
          </button>
          <ScrollArea className="max-h-[360px] pr-2">
            <TooltipProvider>
            <div className="space-y-2">
              {RECIPE_PRESETS.map((recipe) => {
                const isSelected = selected?.id === recipe.id;
                return (
                  <button
                    key={recipe.id}
                    onClick={() => handleSelect(recipe)}
                    disabled={disabled}
                    className={cn(
                      "w-full rounded-md border px-3 py-2.5 text-left transition-colors hover:bg-secondary/50",
                      isSelected ? "border-primary ring-1 ring-primary" : "border-border",
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm font-medium">{recipe.name}</span>
                          <span
                            className={cn(
                              "rounded px-1 py-0.5 text-[10px] font-medium uppercase leading-none",
                              engineColors[recipe.preferredEngine] ?? "text-muted-foreground",
                            )}
                          >
                            {recipe.preferredEngine}
                          </span>
                        </div>
                        <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                          {recipe.description}
                        </p>
                      </div>
                    </div>

                    {/* Engine badges */}
                    {recipe.engineBadges.length > 0 && (
                      <div className="mt-1.5 flex flex-wrap gap-1">
                        {recipe.engineBadges.map((badge) => (
                          <Tooltip key={`${badge.engine}-${badge.label}`}>
                            <TooltipTrigger asChild>
                              <Badge
                                variant={badgeVariantMap[badge.variant ?? ""] ?? "outline"}
                                className={cn(
                                  "cursor-default gap-1 text-[10px]",
                                  engineColors[badge.engine] ?? "",
                                )}
                              >
                                {badge.engine}
                              </Badge>
                            </TooltipTrigger>
                            <TooltipContent>{badge.label}</TooltipContent>
                          </Tooltip>
                        ))}
                      </div>
                    )}

                    {/* Use cases */}
                    {recipe.useCases.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {recipe.useCases.slice(0, 3).map((uc) => (
                          <span
                            key={uc}
                            className="rounded bg-primary/5 px-1.5 py-0.5 text-[10px] text-primary/70"
                          >
                            {uc}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Tags */}
                    {recipe.tags.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {recipe.tags.slice(0, 4).map((tag) => (
                          <span
                            key={tag}
                            className="rounded bg-secondary/40 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Motion hints — shown when selected */}
                    {isSelected && (
                      <div className="mt-1.5 space-y-0.5 text-[10px] text-muted-foreground">
                        <span className="italic">In: {recipe.motionHints.entrance}</span>
                        <br />
                        <span className="italic">Out: {recipe.motionHints.exit}</span>
                      </div>
                    )}

                    {/* Review hints — shown when selected */}
                    {isSelected && recipe.reviewHints.length > 0 && (
                      <div className="mt-1.5 space-y-0.5">
                        {recipe.reviewHints.map((hint, i) => (
                          <div key={i} className="flex items-start gap-1 text-[10px] text-amber-600 dark:text-amber-400">
                            <span>⚠</span>
                            <span>{hint}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
            </TooltipProvider>
          </ScrollArea>
        </CardContent>
      )}
    </Card>
  );
}

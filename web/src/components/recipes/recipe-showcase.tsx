import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { RECIPE_PRESETS } from "@/contracts/create";
import type { RecipeEngineBadge } from "@/contracts/create";

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

function EngineBadgeRow({ badges }: { badges: RecipeEngineBadge[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {badges.map((b) => (
        <Tooltip key={`${b.engine}-${b.label}`}>
          <TooltipTrigger asChild>
            <Badge
              variant={badgeVariantMap[b.variant ?? ""] ?? "outline"}
              className={cn("cursor-default gap-1 text-xs", engineColors[b.engine] ?? "")}
            >
              {b.engine}
            </Badge>
          </TooltipTrigger>
          <TooltipContent>{b.label}</TooltipContent>
        </Tooltip>
      ))}
    </div>
  );
}

function RecipeCard({ recipe }: { recipe: (typeof RECIPE_PRESETS)[number] }) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-base">{recipe.name}</CardTitle>
            <CardDescription className="line-clamp-2">{recipe.description}</CardDescription>
          </div>
          <Badge
            variant="outline"
            className={cn("shrink-0 text-xs", engineColors[recipe.preferredEngine] ?? "")}
          >
            {recipe.preferredEngine}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 space-y-3">
        {/* Engine badges */}
        <div>
          <span className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Engines
          </span>
          <EngineBadgeRow badges={recipe.engineBadges} />
        </div>

        {/* Use cases */}
        <div>
          <span className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Use cases
          </span>
          <div className="flex flex-wrap gap-1">
            {recipe.useCases.map((uc) => (
              <span
                key={uc}
                className="rounded bg-primary/5 px-2 py-0.5 text-xs text-primary/70"
              >
                {uc}
              </span>
            ))}
          </div>
        </div>

        {/* Motion hints */}
        <div>
          <span className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Motion
          </span>
          <div className="space-y-0.5 text-xs text-muted-foreground">
            <p>
              <span className="font-medium text-foreground/70">In:</span> {recipe.motionHints.entrance}
            </p>
            <p>
              <span className="font-medium text-foreground/70">Out:</span> {recipe.motionHints.exit}
            </p>
          </div>
        </div>

        {/* Review hints */}
        <div>
          <span className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Review hints
          </span>
          <ul className="space-y-1">
            {recipe.reviewHints.map((hint, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-amber-600 dark:text-amber-400">
                <span className="mt-0.5 shrink-0">⚠</span>
                <span>{hint}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Tags */}
        {recipe.tags.length > 0 && (
          <div>
            <span className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Tags
            </span>
            <div className="flex flex-wrap gap-1">
              {recipe.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded bg-secondary/40 px-1.5 py-0.5 text-[10px] text-muted-foreground"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Inputs */}
        {recipe.allowedInputs.length > 0 && (
          <div>
            <span className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Inputs
            </span>
            <div className="space-y-1">
              {recipe.allowedInputs.map((inp) => (
                <div
                  key={inp.key}
                  className="flex items-center gap-2 rounded bg-secondary/20 px-2 py-1 text-xs"
                >
                  <code className="rounded bg-secondary/50 px-1 font-mono text-[10px]">{inp.key}</code>
                  <span className="text-muted-foreground">{inp.type}</span>
                  {inp.required && <span className="text-[10px] text-destructive">*required</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function RecipeShowcase() {
  return (
    <TooltipProvider>
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Recipes</h1>
          <p className="text-sm text-muted-foreground">
            {RECIPE_PRESETS.length} showcase patterns — pick one to guide scene structure
          </p>
        </div>

        <Separator />

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {RECIPE_PRESETS.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>

        <div className="rounded-lg border bg-secondary/10 p-4 text-xs text-muted-foreground">
          <span className="font-medium text-foreground">ℹ</span> Recipes define scene kind, preferred engine,
          motion transitions, and input schema. Engine badges show primary and fallback renderers. Review hints
          flag quality gates for each pattern.
        </div>
      </div>
    </TooltipProvider>
  );
}

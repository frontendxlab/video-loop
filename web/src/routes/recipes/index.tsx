import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/recipes/")({
  component: () => (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Recipes</h1>
        <p className="text-sm text-muted-foreground">Recipe registry and showcase patterns</p>
      </div>
      <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">Recipe explorer appears here</div>
    </div>
  ),
});

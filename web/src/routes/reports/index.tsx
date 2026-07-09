import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/reports/")({
  component: () => (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
        <p className="text-sm text-muted-foreground">Video reports, provenance, and per-scene results</p>
      </div>
      <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">Reports viewer appears here</div>
    </div>
  ),
});

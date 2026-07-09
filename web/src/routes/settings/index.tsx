import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/settings/")({
  component: () => (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Provider, model, and queue configuration</p>
      </div>
      <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">Settings form appears here</div>
    </div>
  ),
});

import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/create/")({
  component: () => (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Create</h1>
        <p className="text-sm text-muted-foreground">Prompt input, grill panel, and director preview</p>
      </div>
      <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">
        Prompt input and recipe selection appear here
      </div>
    </div>
  ),
});

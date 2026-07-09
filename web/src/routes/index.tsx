import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: () => null,
  loader: () => { throw redirect({ to: "/jobs" }) },
});

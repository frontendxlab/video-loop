import { createFileRoute } from "@tanstack/react-router";
import { SettingsPage } from "@/lib/contracts/settings-page";

export const Route = createFileRoute("/settings/")({
  component: SettingsPage,
});

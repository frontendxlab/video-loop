import { createFileRoute } from "@tanstack/react-router";
import { CreatePage } from "@/components/create-flow/create-page";

export const Route = createFileRoute("/create/")({
  component: CreatePage,
});

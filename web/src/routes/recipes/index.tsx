import { createFileRoute } from "@tanstack/react-router";
import { RecipeShowcase } from "@/components/recipes/recipe-showcase";

export const Route = createFileRoute("/recipes/")({
  component: RecipeShowcase,
});

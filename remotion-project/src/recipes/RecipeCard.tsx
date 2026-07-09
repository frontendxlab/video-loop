/**
 * RecipeCard — display card for a single recipe.
 *
 * Shows: name, description, engine badges, scene kind tags,
 * use-case pills, and preview text.  Click / keyboard-selectable
 * for later integration with Create flow.
 */

import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { colors, spacing } from "../design-tokens";
import type { Recipe } from "./types";

export interface RecipeCardProps {
  recipe: Recipe;
  /** Called when user clicks "Select" or the whole card. */
  onSelect?: (recipe: Recipe) => void;
  /** Visual mode. */
  variant?: "default" | "compact";
  /** Selected state (picked in create flow). */
  selected?: boolean;
}

const engineColorMap: Record<string, string> = {
  remotion: "#6C5CE7",
  manim: "#00B894",
  animotion: "#FDCB6E",
};

export const RecipeCard: React.FC<RecipeCardProps> = ({
  recipe,
  onSelect,
  variant = "default",
  selected = false,
}) => {
  const handleSelect = () => onSelect?.(recipe);

  const containerStyle: React.CSSProperties = {
    ...(selected
      ? {
          outline: `2px solid ${colors.primary}`,
          outlineOffset: -2,
        }
      : {}),
    opacity: selected ? 1 : undefined,
  };

  return (
    <Card interactive onClick={handleSelect} style={containerStyle}>
      <CardHeader>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: spacing.sm }}>
          <CardTitle>{recipe.name}</CardTitle>
          {/* Engine badges */}
          {variant !== "compact" && (
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap", flexShrink: 0 }}>
              {recipe.engines.map((e) => (
                <Badge key={e} variant="engine" style={{ backgroundColor: (engineColorMap[e] ?? colors.primary) + "20", color: engineColorMap[e] ?? colors.primary, borderColor: (engineColorMap[e] ?? colors.primary) + "40" } as React.CSSProperties}>
                  {e}
                </Badge>
              ))}
            </div>
          )}
        </div>
        <CardDescription>{recipe.description}</CardDescription>
      </CardHeader>

      <CardContent>
        {/* Preview text */}
        {variant !== "compact" && (
          <p style={{ fontSize: 13, lineHeight: "20px", color: colors.textMuted, margin: "0 0 12px 0", fontStyle: "italic" }}>
            {recipe.previewText}
          </p>
        )}

        {/* Scene kind tags */}
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 8 }}>
          {recipe.sceneKinds.map((k) => (
            <Badge key={k} variant="scene">{k}</Badge>
          ))}
        </div>

        {/* Use-case pills */}
        {variant !== "compact" && (
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {recipe.useCases.map((u) => (
              <Badge key={u} variant="useCase">{u}</Badge>
            ))}
          </div>
        )}
      </CardContent>

      <CardFooter>
        <Button
          variant={selected ? "default" : "outline"}
          size="sm"
          onClick={(e) => { e.stopPropagation(); handleSelect(); }}
        >
          {selected ? "Selected" : "Select"}
        </Button>
      </CardFooter>
    </Card>
  );
};

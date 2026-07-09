/**
 * RecipesPage — full explorer page for showcase-inspired recipes.
 *
 * Intended to be mounted as a route in the TanStack Start app.
 * Shows recipe list with filtering, selection for Create flow.
 */

import React, { useState } from "react";
import { colors, fonts, spacing } from "../design-tokens";
import { RecipeList } from "./RecipeList";
import { Button } from "../components/ui/button";
import type { Recipe } from "./types";

export interface RecipesPageProps {
  /** Called when user confirms selected recipes. */
  onConfirm?: (selected: Recipe[]) => void;
  /** Max selections (0 = unlimited). */
  maxSelections?: number;
  /** Show as modal/dialog overlay. */
  embedded?: boolean;
}

export const RecipesPage: React.FC<RecipesPageProps> = ({
  onConfirm,
  maxSelections = 0,
  embedded = false,
}) => {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectedRecipes, setSelectedRecipes] = useState<Recipe[]>([]);

  const isAtLimit = maxSelections > 0 && selectedIds.size >= maxSelections;

  const handleSelect = (recipe: Recipe) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(recipe.id)) {
        next.delete(recipe.id);
        setSelectedRecipes((r) => r.filter((x) => x.id !== recipe.id));
      } else {
        if (maxSelections > 0 && next.size >= maxSelections) {
          // Replace the oldest selection
          const first = [...next][0];
          next.delete(first);
          setSelectedRecipes((r) => r.filter((x) => x.id !== first));
        }
        next.add(recipe.id);
        setSelectedRecipes((r) => [...r, recipe]);
      }
      return next;
    });
  };

  const pageStyle: React.CSSProperties = embedded
    ? { width: "100%", height: "100%", overflow: "auto" }
    : {
        minHeight: "100vh",
        background: colors.background,
        color: colors.text,
        fontFamily: fonts.sans,
        padding: spacing.xl,
        boxSizing: "border-box",
      };

  return (
    <div style={pageStyle}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: spacing.lg,
          gap: spacing.md,
        }}
      >
        <div>
          <h1
            style={{
              fontSize: 28,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              margin: 0,
              color: colors.text,
            }}
          >
            Recipe Explorer
          </h1>
          <p style={{ fontSize: 14, color: colors.textMuted, margin: "4px 0 0 0" }}>
            Browse showcase-inspired video recipes. Select one or more to start building.
          </p>
        </div>

        {onConfirm && (
          <Button
            variant={selectedIds.size > 0 ? "default" : "secondary"}
            size="lg"
            onClick={() => onConfirm(selectedRecipes)}
            disabled={selectedIds.size === 0}
          >
            {selectedIds.size === 0
              ? "Select a recipe"
              : `Use ${selectedIds.size} recipe${selectedIds.size > 1 ? "s" : ""}`}
          </Button>
        )}
      </div>

      {/* Selection info */}
      {maxSelections > 0 && (
        <div
          style={{
            fontSize: 12,
            color: colors.textSubtle,
            marginBottom: spacing.md,
            padding: "8px 12px",
            borderRadius: 8,
            background: colors.chromePanel,
            display: "inline-block",
          }}
        >
          {selectedIds.size}/{maxSelections} selected
          {isAtLimit ? " (max reached — selecting a new one replaces the oldest)" : ""}
        </div>
      )}

      {/* Recipe list */}
      <RecipeList
        onSelect={handleSelect}
        selectedIds={selectedIds}
        showFilters={true}
        layout="grid"
      />
    </div>
  );
};

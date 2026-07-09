/**
 * RecipeList — grid/list of recipe cards with optional filtering.
 *
 * Supports filter by engine and/or scene kind + search by text.
 * Responsive grid layout.
 */

import React, { useMemo, useState } from "react";
import { colors, spacing } from "../design-tokens";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { RecipeCard } from "./RecipeCard";
import {
  recipeRegistry,
  getAllEngines,
  getAllSceneKinds,
} from "./registry";
import type { Recipe } from "./types";

export interface RecipeListProps {
  /** Recipes to display (defaults to full sorted registry). */
  recipes?: Recipe[];
  /** Called when user selects a recipe. */
  onSelect?: (recipe: Recipe) => void;
  /** Currently selected recipe ids. */
  selectedIds?: Set<string>;
  /** Show filter bar. */
  showFilters?: boolean;
  /** Layout: grid or list. */
  layout?: "grid" | "list";
  /** Max items to show (0 = all). */
  maxItems?: number;
}

export const RecipeList: React.FC<RecipeListProps> = ({
  recipes,
  onSelect,
  selectedIds = new Set(),
  showFilters = true,
  layout = "grid",
  maxItems = 0,
}) => {
  const allRecipes = recipes ?? recipeRegistry;
  const [engineFilter, setEngineFilter] = useState<string | null>(null);
  const [kindFilter, setKindFilter] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showAllKinds, setShowAllKinds] = useState(false);

  const allEngines = useMemo(() => getAllEngines(), []);
  const allSceneKinds = useMemo(() => getAllSceneKinds(), []);

  const visibleKinds = showAllKinds ? allSceneKinds : allSceneKinds.slice(0, 8);

  const filtered = useMemo(() => {
    let result = allRecipes;
    if (engineFilter) result = result.filter((r) => r.engines.includes(engineFilter as any));
    if (kindFilter) result = result.filter((r) => r.sceneKinds.includes(kindFilter as any));
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          r.description.toLowerCase().includes(q) ||
          r.previewText.toLowerCase().includes(q) ||
          r.useCases.some((u) => u.toLowerCase().includes(q)),
      );
    }
    // Sort by weight desc
    result = [...result].sort((a, b) => (b.sortWeight ?? 0) - (a.sortWeight ?? 0));
    if (maxItems > 0) result = result.slice(0, maxItems);
    return result;
  }, [allRecipes, engineFilter, kindFilter, search, maxItems]);

  const gridStyle: React.CSSProperties = {
    display: "grid",
    gridTemplateColumns: layout === "grid"
      ? "repeat(auto-fill, minmax(340px, 1fr))"
      : "1fr",
    gap: spacing.md,
  };

  return (
    <div style={{ width: "100%" }}>
      {/* Filter bar */}
      {showFilters && (
        <div style={{ marginBottom: spacing.lg }}>
          {/* Search */}
          <input
            type="text"
            placeholder="Search recipes…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: "100%",
              padding: "10px 14px",
              borderRadius: 8,
              border: `1px solid ${colors.chromeBorder}`,
              background: colors.chromePanel,
              color: colors.text,
              fontSize: 14,
              outline: "none",
              boxSizing: "border-box",
              marginBottom: spacing.md,
            }}
          />

          {/* Engine filter chips */}
          <div style={{ marginBottom: spacing.sm }}>
            <span style={{ fontSize: 12, color: colors.textSubtle, marginRight: 8 }}>Engine:</span>
            <div style={{ display: "inline-flex", gap: 4, flexWrap: "wrap" }}>
              <Button
                variant={engineFilter === null ? "default" : "secondary"}
                size="sm"
                onClick={() => setEngineFilter(null)}
              >
                All
              </Button>
              {allEngines.map((e) => (
                <Button
                  key={e}
                  variant={engineFilter === e ? "default" : "secondary"}
                  size="sm"
                  onClick={() => setEngineFilter(e === engineFilter ? null : e)}
                >
                  {e}
                </Button>
              ))}
            </div>
          </div>

          {/* Scene kind filter chips */}
          <div>
            <span style={{ fontSize: 12, color: colors.textSubtle, marginRight: 8 }}>Kind:</span>
            <div style={{ display: "inline-flex", gap: 4, flexWrap: "wrap" }}>
              <Button
                variant={kindFilter === null ? "default" : "secondary"}
                size="sm"
                onClick={() => setKindFilter(null)}
              >
                All
              </Button>
              {visibleKinds.map((k) => (
                <Button
                  key={k}
                  variant={kindFilter === k ? "default" : "secondary"}
                  size="sm"
                  onClick={() => setKindFilter(k === kindFilter ? null : k)}
                >
                  {k}
                </Button>
              ))}
              {!showAllKinds && allSceneKinds.length > 8 && (
                <Button variant="ghost" size="sm" onClick={() => setShowAllKinds(true)}>
                  +{allSceneKinds.length - 8} more
                </Button>
              )}
            </div>
          </div>

          {/* Results count */}
          <div style={{ fontSize: 12, color: colors.textSubtle, marginTop: spacing.sm }}>
            {filtered.length} recipe{filtered.length !== 1 ? "s" : ""}
            {(engineFilter || kindFilter || search) && " (filtered)"}
          </div>
        </div>
      )}

      {/* Card grid */}
      {filtered.length === 0 ? (
        <div style={{ textAlign: "center", padding: spacing.xxl, color: colors.textMuted }}>
          No recipes match your filters.
        </div>
      ) : (
        <div style={gridStyle}>
          {filtered.map((r) => (
            <RecipeCard
              key={r.id}
              recipe={r}
              onSelect={onSelect}
              selected={selectedIds.has(r.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

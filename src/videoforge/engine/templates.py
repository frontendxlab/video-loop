"""Video template registry — genre-level templates with scene plans.

Each template defines a multi-scene structure for a video genre.
Used by grill to suggest templates based on prompt keywords.
Deterministic: same prompt → same template suggestions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TemplateScene:
    """A single scene within a video template."""

    scene_type: str
    title: str
    description: str
    duration_seconds: float = 4.0


@dataclass(frozen=True)
class VideoTemplate:
    """A genre-level video template with a multi-scene plan."""

    id: str
    name: str
    description: str
    icon: str
    category: str
    scenes: tuple[TemplateScene, ...]
    tags: tuple[str, ...]


TEMPLATE_REGISTRY: tuple[VideoTemplate, ...] = (
    VideoTemplate(
        id="explainer",
        name="Explainer",
        description="Explain concept with diagrams, key points, and clear narration",
        icon="lightbulb",
        category="educational",
        scenes=(
            TemplateScene("title", "Topic Intro", "Opening title introducing the topic"),
            TemplateScene("diagram", "How It Works", "Visual diagram explaining core concept"),
            TemplateScene("bullets", "Key Takeaways", "Main takeaways highlighted in bullet form"),
            TemplateScene("outro", "Summary & Next Steps", "Recap and further resources"),
        ),
        tags=("explain", "concept", "introduction", "overview", "educational"),
    ),
    VideoTemplate(
        id="tutorial",
        name="Tutorial",
        description="Step-by-step walkthrough with examples and clear instructions",
        icon="book-open",
        category="educational",
        scenes=(
            TemplateScene("title", "Tutorial Title", "Opening title with topic and goal"),
            TemplateScene("code", "Step-by-Step", "Walk through implementation with code examples"),
            TemplateScene("bullets", "Key Takeaways", "Important points highlighted"),
            TemplateScene("outro", "Next Steps", "Where to go from here"),
        ),
        tags=("tutorial", "walkthrough", "how-to", "guide", "steps", "learn"),
    ),
    VideoTemplate(
        id="product-demo",
        name="Product Demo",
        description="Showcase product features with callouts, comparisons, and CTA",
        icon="monitor",
        category="marketing",
        scenes=(
            TemplateScene("title", "Product Intro", "Opening with product name and tagline"),
            TemplateScene("comparison", "Feature 1", "First key feature with highlight callouts"),
            TemplateScene("comparison", "Feature 2", "Second key feature demonstration"),
            TemplateScene("outro", "Call to Action", "CTA with next steps for the viewer"),
        ),
        tags=("product", "demo", "showcase", "feature", "marketing"),
    ),
    VideoTemplate(
        id="marketing",
        name="Marketing",
        description="Promotional video with hook, problem-solution, and strong CTA",
        icon="megaphone",
        category="marketing",
        scenes=(
            TemplateScene("title", "Hook", "Attention-grabbing opening hook"),
            TemplateScene("bullets", "The Problem", "Problem statement that resonates"),
            TemplateScene("comparison", "The Solution", "Solution presented with before/after"),
            TemplateScene("outro", "Call to Action", "Strong closing with CTA"),
        ),
        tags=("marketing", "promo", "promotional", "hype", "campaign"),
    ),
    VideoTemplate(
        id="storytelling",
        name="Storytelling",
        description="Narrative-driven video with emotional arc and story structure",
        icon="scroll-text",
        category="narrative",
        scenes=(
            TemplateScene("title", "Setup", "Establish context and characters"),
            TemplateScene("bullets", "Conflict", "Present the challenge or stakes"),
            TemplateScene("quote", "Resolution", "Climax and resolution of the story"),
            TemplateScene("outro", "Reflection", "Closing reflections and call to action"),
        ),
        tags=("story", "narrative", "emotional", "journey", "arc"),
    ),
    VideoTemplate(
        id="data-story",
        name="Data Story",
        description="Data-driven narrative with charts, metrics, and insights",
        icon="bar-chart-3",
        category="data",
        scenes=(
            TemplateScene("title", "Context", "Set the data context and motivation"),
            TemplateScene("chart", "Data Overview", "Key metrics and data visualization"),
            TemplateScene("chart", "Deep Dive", "Detailed breakdown of specific data points"),
            TemplateScene("bullets", "Insights", "Actionable insights and conclusions"),
        ),
        tags=("data", "chart", "metrics", "analytics", "statistics", "insights"),
    ),
    VideoTemplate(
        id="comparison",
        name="Comparison",
        description="Side-by-side comparison of options, versions, or approaches",
        icon="git-compare",
        category="analysis",
        scenes=(
            TemplateScene("title", "Comparison Intro", "What is being compared and why"),
            TemplateScene("comparison", "Option A", "Overview of the first option"),
            TemplateScene("comparison", "Option B", "Overview of the second option"),
            TemplateScene("diff", "Verdict", "Summary verdict and recommendation"),
        ),
        tags=("compare", "comparison", "vs", "versus", "difference", "migration"),
    ),
    VideoTemplate(
        id="timeline",
        name="Timeline",
        description="Chronological walkthrough of events, history, or roadmap",
        icon="clock",
        category="narrative",
        scenes=(
            TemplateScene("title", "Timeline Intro", "Opening with the scope of events"),
            TemplateScene("timeline", "Event 1", "First key event or milestone"),
            TemplateScene("timeline", "Event 2", "Second key event or milestone"),
            TemplateScene("timeline", "Event 3", "Third key event or milestone"),
            TemplateScene("outro", "Summary & Outlook", "Wrap-up and future outlook"),
        ),
        tags=("timeline", "history", "roadmap", "events", "chronological"),
    ),
    VideoTemplate(
        id="review",
        name="Review",
        description="Honest review with pros/cons, rating, and final verdict",
        icon="star",
        category="analysis",
        scenes=(
            TemplateScene("title", "Review Intro", "What is being reviewed"),
            TemplateScene("bullets", "The Good", "What works well — pros"),
            TemplateScene("bullets", "The Bad", "What could be improved — cons"),
            TemplateScene("outro", "Final Verdict", "Rating and final recommendation"),
        ),
        tags=("review", "rating", "pros-cons", "verdict", "opinion"),
    ),
)

_TEMPLATE_MAP: dict[str, VideoTemplate] = {t.id: t for t in TEMPLATE_REGISTRY}


def get_template(template_id: str) -> VideoTemplate | None:
    """Lookup template by id. Returns None if not found."""
    return _TEMPLATE_MAP.get(template_id)


def list_templates() -> tuple[VideoTemplate, ...]:
    """Return all registered templates."""
    return TEMPLATE_REGISTRY


def suggest_templates(
    prompt: str,
    max_suggestions: int = 3,
) -> list[dict[str, Any]]:
    """Suggest templates based on keyword matching against template tags.

    Returns list of dicts with id, name, description, icon, match_reason,
    scene_count — sorted by match strength descending, limited to max_suggestions.
    """
    tokens = set(
        re.findall(r"[a-z]\w+", prompt.lower())
    )

    scored: list[tuple[float, dict[str, Any]]] = []
    for t in TEMPLATE_REGISTRY:
        tag_overlap = tokens & set(t.tags)
        if not tag_overlap:
            continue

        # Score = proportion of matching tags weighted by match count
        score = len(tag_overlap) / max(len(t.tags), 1)
        # Bonus for exact tag matches
        exact = prompt.lower().count(t.id.replace("-", " "))
        score += exact * 0.5

        match_words = sorted(tag_overlap, key=lambda w: len(w), reverse=True)
        reason = f"Matches: {', '.join(match_words[:3])}"

        scored.append((
            score,
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "icon": t.icon,
                "category": t.category,
                "match_reason": reason,
                "scene_count": len(t.scenes),
            },
        ))

    scored.sort(key=lambda x: (-x[0], x[1]["name"]))
    return [item[1] for item in scored[:max_suggestions]]

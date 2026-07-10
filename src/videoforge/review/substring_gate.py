"""HighlightSubstringGate — deterministic substring-presence check.

Validates that a focus/highlight phrase is present as a substring within
a body text snippet.  No AI dependency.

Scenarios (document-highlight):
  - ``focus_phrase`` must be a non-empty string.
  - ``body_snippet`` must be a non-empty string.
  - ``focus_phrase`` must appear as an exact substring of ``body_snippet``
    (case-sensitive by default).
"""

from __future__ import annotations

from typing import Any


class HighlightSubstringGate:
    """Deterministic highlight substring presence review gate.

    Checks that a focus phrase appears as a substring within a body text
    snippet.  Pure Python, no AI or video I/O.

    Typical usage::

        gate = HighlightSubstringGate()
        result = gate.run({
            "focus_phrase": "important result",
            "body_snippet": "The study found an important result in all cases",
        })
        if not result["passed"]:
            for issue in result["issues"]:
                print(issue["type"], issue["detail"])
    """

    # ── Public entry point ────────────────────────────────────────────────

    @staticmethod
    def run(
        scene_payload: dict[str, Any],
        case_sensitive: bool = True,
    ) -> dict[str, Any]:
        """Run substring-presence checks on scene payload.

        Args:
            scene_payload: Dict of scene props.  Supported keys:
                ``focus_phrase``, ``focus_text``, ``highlight_text``
                (the substring to find), and ``body_snippet``, ``body_text``,
                ``source_text`` (the text to search within).
            case_sensitive: Whether the substring match is case-sensitive.
                Defaults to True.

        Returns:
            Dict with keys ``issues`` (list of issue dicts) and ``passed``.
        """
        issues: list[dict[str, Any]] = []

        # Resolve focus phrase from supported keys
        focus_phrase = (
            scene_payload.get("focus_phrase")
            or scene_payload.get("focus_text")
            or scene_payload.get("highlight_text")
            or ""
        )
        # Resolve body text from supported keys
        body_snippet = (
            scene_payload.get("body_snippet")
            or scene_payload.get("body_text")
            or scene_payload.get("source_text")
            or ""
        )

        if not isinstance(focus_phrase, str) or focus_phrase.strip() == "":
            issues.append({
                "type": "focus_phrase_empty",
                "detail": "focus_phrase is missing, empty, or not a string",
                "severity": "high",
            })
            # Can't proceed without a phrase
            return {"issues": issues, "passed": False}

        if not isinstance(body_snippet, str) or body_snippet.strip() == "":
            issues.append({
                "type": "body_snippet_empty",
                "detail": "body_snippet is missing, empty, or not a string",
                "severity": "high",
            })
            # Can't proceed without body text
            return {"issues": issues, "passed": False}

        # Core check: substring presence
        if case_sensitive:
            found = focus_phrase in body_snippet
        else:
            found = focus_phrase.lower() in body_snippet.lower()

        if not found:
            match_mode = "case-sensitive" if case_sensitive else "case-insensitive"
            issues.append({
                "type": "focus_phrase_not_found",
                "detail": (
                    f"focus_phrase \"{focus_phrase}\" is not a substring of "
                    f"body_snippet ({match_mode} match)"
                ),
                "severity": "high",
                "case_sensitive": case_sensitive,
            })

        return {"issues": issues, "passed": len(issues) == 0}

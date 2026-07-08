"""Fact-checking utility for verifying script claims against source code."""

from __future__ import annotations

import re
from typing import Any


class FactChecker:
    """Validates factual claims in scripts against source code diffs."""

    BEHAVIOR_WORDS: set[str] = {
        "validates", "checks", "returns", "throws", "processes",
    }

    def extract_claims(self, script: str) -> list[dict[str, str]]:
        """Parse script text and extract factual claims."""
        if not script:
            return []

        claims: list[dict[str, str]] = []
        seen: set[str] = set()

        # Function claims: words followed by (
        for m in re.finditer(r'\b(\w+)\s*\(', script):
            name = m.group(1)
            if name not in seen:
                claims.append({"text": name, "type": "function"})
                seen.add(name)

        # Function claims: words preceding "function"
        for m in re.finditer(r'\b(\w+)\s+function\b', script):
            name = m.group(1)
            if name not in seen:
                claims.append({"text": name, "type": "function"})
                seen.add(name)

        # Behavior claims
        for word in self.BEHAVIOR_WORDS:
            if word in script and word not in seen:
                claims.append({"text": word, "type": "behavior"})
                seen.add(word)

        # API claims: 3-digit status codes
        for m in re.finditer(r'\b(\d{3})\b', script):
            code = m.group(1)
            if code not in seen:
                claims.append({"text": code, "type": "api"})
                seen.add(code)

        return claims

    def verify_claim(self, claim: dict[str, str], source_diff: str) -> dict[str, str]:
        """Verify if a claim is supported by the source diff."""
        if claim["text"] in source_diff:
            return {"status": "verified", "evidence": "found in diff"}
        return {"status": "fail", "evidence": "not found in diff"}

    def check_script(
        self, script: str, source_diff: str, mode: str = "advisory"
    ) -> dict[str, Any]:
        """Full fact check of a script against source diff."""
        claims = self.extract_claims(script)
        result_claims: list[dict[str, str]] = []
        any_failed = False

        for claim in claims:
            result = self.verify_claim(claim, source_diff)
            result_claims.append({
                "text": claim["text"],
                "type": claim["type"],
                "status": result["status"],
                "evidence": result["evidence"],
            })
            if result["status"] == "fail":
                any_failed = True

        return {
            "claims": result_claims,
            "blocked": any_failed if mode == "blocking" else False,
        }

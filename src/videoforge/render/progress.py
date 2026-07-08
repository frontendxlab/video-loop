"""Remotion stdout progress parser."""

from __future__ import annotations

import re
from typing import Optional


class ProgressParser:
    """Parses frame progress lines from Remotion stdout."""

    _pattern = re.compile(r"Frame:\s*(\d+)/(\d+)")

    def parse_line(self, line: str) -> Optional[dict]:
        match = self._pattern.search(line)
        if match:
            return {"current": int(match.group(1)), "total": int(match.group(2))}
        return None

from __future__ import annotations

import re


class BaseFetcher:
    @staticmethod
    def validate_github_url(url: str) -> bool:
        pattern = r"^https://github\.com/([^/]+)/([^/]+)/(pull|issues)/(\d+)$"
        return re.match(pattern, url) is not None

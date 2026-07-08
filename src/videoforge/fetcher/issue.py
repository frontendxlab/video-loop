from __future__ import annotations

import json
import re

from videoforge.exceptions import GitHubAuthError, GitHubNetworkError
from videoforge.fetcher.base import BaseFetcher
from videoforge.fetcher.gh_cli import GhCLI


class IssueFetcher(BaseFetcher):
    def fetch(self, url: str) -> dict:
        if not self.validate_github_url(url):
            raise ValueError(f"Invalid GitHub URL: {url}")

        match = re.match(
            r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)$", url
        )
        if not match:
            raise ValueError(f"Not a GitHub issue URL: {url}")

        cli = GhCLI()

        try:
            result = cli.run([
                "issue", "view", url,
                "--json", "title,body,author,labels,comments,state",
            ])
            return json.loads(result)
        except (GitHubAuthError, GitHubNetworkError):
            raise

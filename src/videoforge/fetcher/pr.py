from __future__ import annotations

import json
import re

from videoforge.exceptions import GitHubAuthError, GitHubNetworkError
from videoforge.fetcher.base import BaseFetcher
from videoforge.fetcher.gh_cli import GhCLI


class PRFetcher(BaseFetcher):
    def fetch(self, url: str) -> dict:
        if not self.validate_github_url(url):
            raise ValueError(f"Invalid GitHub URL: {url}")

        match = re.match(
            r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)$", url
        )
        if not match:
            raise ValueError(f"Not a GitHub PR URL: {url}")

        owner, repo, number = match.group(1), match.group(2), match.group(3)

        cli = GhCLI()

        try:
            pr_info = cli.run([
                "pr", "view", number,
                "--json", "title,body,number,author,labels,comments",
                "-R", f"{owner}/{repo}",
            ])
            result = json.loads(pr_info)

            diff = cli.run(["pr", "diff", number, "-R", f"{owner}/{repo}"])
            result["diff"] = diff

            files_output = cli.run([
                "pr", "view", number,
                "--json", "files",
                "-R", f"{owner}/{repo}",
            ])
            files_data = json.loads(files_output)
            result["files"] = files_data.get("files", [])

            return result
        except (GitHubAuthError, GitHubNetworkError):
            raise

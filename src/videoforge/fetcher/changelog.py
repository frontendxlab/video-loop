from __future__ import annotations

import json
import subprocess

from videoforge.exceptions import GitHubAuthError, GitHubNetworkError
from videoforge.fetcher.base import BaseFetcher
from videoforge.fetcher.gh_cli import GhCLI


class ChangelogFetcher(BaseFetcher):
    def fetch(self, owner: str, repo: str, from_ref: str, to_ref: str = "HEAD") -> dict:
        cli = GhCLI()

        try:
            result = cli.run([
                "api", f"repos/{owner}/{repo}/compare/{from_ref}...{to_ref}",
            ])
            data = json.loads(result)
        except GitHubAuthError:
            raise
        except (subprocess.CalledProcessError, GitHubNetworkError) as e:
            raise GitHubNetworkError(
                f"Failed to fetch changelog for {owner}/{repo}: {e}"
            ) from e

        commits = [
            {
                "sha": c["sha"],
                "message": c["commit"]["message"],
                "author": c.get("author", {}).get("login", c["commit"]["author"]["name"]),
            }
            for c in data.get("commits", [])
        ]
        files_changed = len(data.get("files", []))
        additions = sum(f.get("additions", 0) for f in data.get("files", []))
        deletions = sum(f.get("deletions", 0) for f in data.get("files", []))

        return {
            "commits": commits,
            "files_changed": files_changed,
            "additions": additions,
            "deletions": deletions,
        }

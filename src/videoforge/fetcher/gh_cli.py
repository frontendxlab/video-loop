from __future__ import annotations

import subprocess

from videoforge.exceptions import GitHubAuthError, GitHubNetworkError


class GhCLI:
    def __init__(self) -> None:
        try:
            subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                check=True,
            )
        except FileNotFoundError as e:
            raise GitHubAuthError("GitHub CLI not found") from e
        except subprocess.TimeoutExpired as e:
            raise GitHubNetworkError("Request timed out") from e

    def run(self, args: list[str], timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                ["gh", *args],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
            )
            return result.stdout
        except FileNotFoundError as e:
            raise GitHubAuthError("GitHub CLI not found") from e
        except subprocess.TimeoutExpired as e:
            raise GitHubNetworkError("Request timed out") from e

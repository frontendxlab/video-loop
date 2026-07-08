"""Tests for GitHub PR content fetcher."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from videoforge.exceptions import GitHubAuthError, GitHubNetworkError


@pytest.fixture
def fetcher():
    from videoforge.fetcher.pr import PRFetcher
    return PRFetcher()


class TestPRFetch:
    def test_fetch_returns_pr_data(self, fetcher, mock_subprocess_run):
        result = fetcher.fetch("https://github.com/org/repo/pull/1")
        assert "title" in result
        assert "number" in result

    def test_fetch_extracts_diff(self, fetcher, mock_subprocess_run):
        result = fetcher.fetch("https://github.com/org/repo/pull/1")
        assert "diff" in result

    def test_fetch_extracts_files(self, fetcher, mock_subprocess_run):
        result = fetcher.fetch("https://github.com/org/repo/pull/1")
        assert "files" in result

    def test_raises_auth_error_when_not_logged_in(self, fetcher):
        with patch("subprocess.run") as mock:
            mock.side_effect = FileNotFoundError("gh not found")
            with pytest.raises(GitHubAuthError):
                fetcher.fetch("https://github.com/org/repo/pull/1")

    def test_raises_network_error_on_timeout(self, fetcher):
        import subprocess
        with patch("subprocess.run") as mock:
            mock.side_effect = subprocess.TimeoutExpired("gh", 30)
            with pytest.raises(GitHubNetworkError):
                fetcher.fetch("https://github.com/org/repo/pull/1")


class TestURLValidation:
    def test_validates_pr_url_format(self, fetcher):
        with pytest.raises(ValueError):
            fetcher.fetch("not-a-url")

    def test_validates_github_url(self, fetcher):
        with pytest.raises(ValueError):
            fetcher.fetch("https://example.com/repo/pull/1")

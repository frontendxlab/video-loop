"""Tests for GitHub webhook handler."""

from __future__ import annotations

import hmac
import json
from unittest.mock import patch, MagicMock

import pytest
from videoforge.exceptions import WebhookAuthError


class TestWebhookSignature:
    def test_valid_signature_passes(self):
        from videoforge.github.signature import verify_signature
        secret = b"test-secret"
        payload = b'{"action": "opened", "pull_request": {"url": "https://..."}}'
        sig = "sha256=" + hmac.new(secret, payload, "sha256").hexdigest()
        assert verify_signature(payload, sig, secret) is True

    def test_invalid_signature_fails(self):
        from videoforge.github.signature import verify_signature
        with pytest.raises(WebhookAuthError):
            verify_signature(b"payload", "sha256=bad", b"secret")

    def test_missing_signature_fails(self):
        from videoforge.github.signature import verify_signature
        with pytest.raises(WebhookAuthError):
            verify_signature(b"payload", None, b"secret")


class TestWebhookHandler:
    def test_accepts_pr_opened_event(self):
        from videoforge.github.webhook import handle_webhook
        payload = {"action": "opened", "pull_request": {"html_url": "https://github.com/org/repo/pull/1"}}
        result = handle_webhook(payload, "pull_request")
        assert "job_id" in result

    def test_accepts_issue_opened_event(self):
        from videoforge.github.webhook import handle_webhook
        payload = {"action": "opened", "issue": {"html_url": "https://github.com/org/repo/issues/1"}}
        result = handle_webhook(payload, "issues")
        assert "job_id" in result

    def test_returns_200_on_valid_payload(self):
        from videoforge.github.webhook import handle_webhook
        payload = {"action": "opened", "pull_request": {"html_url": "https://github.com/org/repo/pull/1"}}
        result = handle_webhook(payload, "pull_request")
        assert result is not None

    def test_ignores_unrelated_events(self):
        from videoforge.github.webhook import handle_webhook
        payload = {"action": "labeled"}
        result = handle_webhook(payload, "pull_request")
        assert result is None


class TestPublisher:
    def test_publishes_comment_to_pr(self):
        from videoforge.github.publisher import Publisher
        pub = Publisher()
        with patch.object(pub, "_run_gh") as mock:
            mock.return_value = ""
            result = pub.post_pr_comment("https://github.com/org/repo/pull/1", "Video generated")
        assert result["success"] is True

    def test_publish_comment_format(self):
        from videoforge.github.publisher import Publisher
        pub = Publisher()
        comment = pub.build_comment("Test Video", "/path/to/video.mp4", 120.5)
        assert "Test Video" in comment
        assert ".mp4" in comment
        assert "VideoForge" in comment

    def test_publish_raises_on_auth_error(self):
        from videoforge.github.publisher import Publisher
        pub = Publisher()
        with patch.object(pub, "_run_gh") as mock:
            mock.side_effect = FileNotFoundError("gh not found")
            with pytest.raises(FileNotFoundError):
                pub.post_pr_comment("https://github.com/org/repo/pull/1", "test")

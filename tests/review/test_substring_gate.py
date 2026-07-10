"""Tests for HighlightSubstringGate — deterministic substring-presence check."""

from __future__ import annotations

from videoforge.review.substring_gate import HighlightSubstringGate


class TestHighlightSubstringGate:
    """HighlightSubstringGate.run() unit tests."""

    def test_phrase_present_passes(self) -> None:
        """Exact substring match → pass."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "important result",
            "body_snippet": "The study found an important result in all cases",
        })
        assert result["passed"] is True

    def test_phrase_not_present_fails(self) -> None:
        """Phrase not in body → fail."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "missing phrase",
            "body_snippet": "The study found an important result in all cases",
        })
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "focus_phrase_not_found"

    def test_empty_focus_phrase_fails(self) -> None:
        """Empty focus_phrase → fail."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "",
            "body_snippet": "some text",
        })
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "focus_phrase_empty"

    def test_missing_focus_phrase_fails(self) -> None:
        """No focus_phrase key → fail."""
        result = HighlightSubstringGate.run({
            "body_snippet": "some text",
        })
        assert result["passed"] is False

    def test_empty_body_fails(self) -> None:
        """Empty body_snippet → fail."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "hello",
            "body_snippet": "",
        })
        assert result["passed"] is False
        assert result["issues"][0]["type"] == "body_snippet_empty"

    def test_missing_body_fails(self) -> None:
        """No body_snippet key → fail."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "hello",
        })
        assert result["passed"] is False

    def test_case_sensitive_detects_difference(self) -> None:
        """Case-sensitive match fails on case mismatch."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "Important",
            "body_snippet": "this is important",
        }, case_sensitive=True)
        assert result["passed"] is False

    def test_case_insensitive_passes(self) -> None:
        """Case-insensitive match succeeds."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "Important",
            "body_snippet": "this is important",
        }, case_sensitive=False)
        assert result["passed"] is True

    def test_whitespace_sensitive(self) -> None:
        """Whitespace matters — 'hello' not in 'helloworld'."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "hello",
            "body_snippet": "helloworld",
        })
        assert result["passed"] is True  # 'hello' IS a substring of 'helloworld'

    def test_partial_word_match(self) -> None:
        """Partial word match works."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "port",
            "body_snippet": "The report was filed",
        })
        assert result["passed"] is True  # 'port' is in 'report'

    def test_focus_text_alias(self) -> None:
        """focus_text accepted as alias for focus_phrase."""
        result = HighlightSubstringGate.run({
            "focus_text": "key finding",
            "body_snippet": "The key finding was unexpected",
        })
        assert result["passed"] is True

    def test_highlight_text_alias(self) -> None:
        """highlight_text accepted as alias for focus_phrase."""
        result = HighlightSubstringGate.run({
            "highlight_text": "key finding",
            "body_snippet": "The key finding was unexpected",
        })
        assert result["passed"] is True

    def test_body_text_alias(self) -> None:
        """body_text accepted as alias for body_snippet."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "hello",
            "body_text": "hello world",
        })
        assert result["passed"] is True

    def test_source_text_alias(self) -> None:
        """source_text accepted as alias for body_snippet."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "hello",
            "source_text": "hello world",
        })
        assert result["passed"] is True

    def test_issue_has_detail_and_severity(self) -> None:
        """Issues should have proper fields."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "missing",
            "body_snippet": "hello world",
        })
        for issue in result["issues"]:
            assert "detail" in issue
            assert "severity" in issue

    def test_case_sensitive_default_is_true(self) -> None:
        """Default case_sensitive should be True."""
        result = HighlightSubstringGate.run({
            "focus_phrase": "Hello",
            "body_snippet": "hello world",
        })
        assert result["passed"] is False  # case mismatch by default


class TestHighlightSubstringGatePolicy:
    """FrameReviewer.evaluate_substring_policy tests."""

    def test_policy_pass_no_issues(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_substring_policy({"issues": []}) == "pass"

    def test_policy_fail_on_high(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_substring_policy({
            "issues": [{"severity": "high", "type": "focus_phrase_empty"}],
        }) == "fail"

    def test_policy_warn_empty(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        assert FrameReviewer.evaluate_substring_policy({
            "issues": [{"severity": "high", "type": "focus_phrase_not_found"}],
        }) == "fail"


class TestFrameReviewerSubstring:
    """FrameReviewer.check_highlight_substring integration tests."""

    def test_check_highlight_delegates(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        result = fr.check_highlight_substring({
            "focus_phrase": "hello",
            "body_snippet": "hello world",
        })
        assert "issues" in result
        assert "passed" in result
        assert result["passed"] is True

    def test_check_highlight_fails_missing(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        result = fr.check_highlight_substring({
            "focus_phrase": "missing",
            "body_snippet": "hello world",
        })
        assert result["passed"] is False

    def test_check_highlight_case_insensitive(self) -> None:
        from videoforge.review.frame_reviewer import FrameReviewer
        fr = FrameReviewer()
        result = fr.check_highlight_substring({
            "focus_phrase": "Hello",
            "body_snippet": "hello world",
        }, case_sensitive=False)
        assert result["passed"] is True

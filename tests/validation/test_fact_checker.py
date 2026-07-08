"""Tests for Fact Checker."""

from __future__ import annotations

import pytest


@pytest.fixture
def fact_checker():
    from videoforge.validation.fact_checker import FactChecker
    return FactChecker()


class TestClaimExtraction:
    def test_extracts_function_names(self, fact_checker):
        script = "The authenticate function validates the token."
        claims = fact_checker.extract_claims(script)
        assert any("authenticate" in c["text"] for c in claims)

    def test_extracts_api_endpoints(self, fact_checker):
        script = "The API now returns 401 for invalid tokens."
        claims = fact_checker.extract_claims(script)
        assert any("401" in c["text"] for c in claims)

    def test_extracts_behavioral_claims(self, fact_checker):
        script = "This function validates the session."
        claims = fact_checker.extract_claims(script)
        assert any("validates" in c["text"] for c in claims)

    def test_empty_script_returns_empty_list(self, fact_checker):
        assert fact_checker.extract_claims("") == []


class TestSourceVerification:
    def test_verifies_function_exists_in_diff(self, fact_checker, sample_pr_diff):
        result = fact_checker.verify_claim(
            {"text": "authenticate", "type": "function"},
            sample_pr_diff
        )
        assert result["status"] in ("verified", "warning")

    def test_verifies_missing_function_as_fail(self, fact_checker, sample_pr_diff):
        result = fact_checker.verify_claim(
            {"text": "nonexistentFunction", "type": "function"},
            sample_pr_diff
        )
        assert result["status"] == "fail"


class TestFactCheckReport:
    def test_report_contains_all_claims(self, fact_checker, sample_pr_diff):
        script = "The authenticate function validates tokens."
        report = fact_checker.check_script(script, sample_pr_diff)
        assert "claims" in report
        assert len(report["claims"]) > 0

    def test_l1_mode_does_not_block(self, fact_checker, sample_pr_diff):
        script = "The nonexistentThing processes data."
        report = fact_checker.check_script(script, sample_pr_diff, mode="advisory")
        assert report["blocked"] is False

    def test_l2_mode_blocks_on_failures(self, fact_checker, sample_pr_diff):
        script = "The nonexistentThing processes data."
        report = fact_checker.check_script(script, sample_pr_diff, mode="blocking")
        assert report["blocked"] is True

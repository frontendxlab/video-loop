"""Tests for audio chunker (sentence splitting + token grouping)."""

from __future__ import annotations

import pytest


@pytest.fixture
def chunker():
    from videoforge.audio.chunker import Chunker
    return Chunker(max_tokens_per_chunk=50)


class TestSentenceSplitter:
    def test_splits_simple_sentences(self, chunker):
        result = chunker.split_sentences("Hello world. This is a test. Goodbye!")
        assert result == ["Hello world.", "This is a test.", "Goodbye!"]

    def test_handles_multiple_punctuation(self, chunker):
        result = chunker.split_sentences("Hello! Is this working? Yes it is.")
        assert result == ["Hello!", "Is this working?", "Yes it is."]

    def test_returns_empty_list_for_empty_string(self, chunker):
        assert chunker.split_sentences("") == []

    def test_handles_abbreviations(self, chunker):
        result = chunker.split_sentences("Dr. Smith said etc. It works.")
        assert len(result) >= 2
        assert "It works." in result[-1]

    def test_single_sentence_no_trailing_punctuation(self, chunker):
        result = chunker.split_sentences("Hello world")
        assert result == ["Hello world"]


class TestTokenCounter:
    def test_counts_approx_tokens(self, chunker):
        count = chunker.count_tokens("Hello world")
        assert 2 <= count <= 5

    def test_zero_for_empty_string(self, chunker):
        assert chunker.count_tokens("") == 0

    def test_longer_text_has_more_tokens(self, chunker):
        short = chunker.count_tokens("A B C D E")
        long = chunker.count_tokens("A B C D E F G H I J K L M N O P")
        assert long > short


class TestChunkGrouper:
    def test_combines_short_sentences(self, chunker):
        chunks = chunker.group_into_chunks(["A.", "B.", "C."])
        assert len(chunks) == 1

    def test_respects_token_limit(self, chunker):
        chunker.max_tokens_per_chunk = 10
        sentences = ["This is a long sentence that will exceed the token limit for sure."]
        chunks = chunker.group_into_chunks(sentences)
        for c in chunks:
            assert chunker.count_tokens(c) <= 10

    def test_splits_long_sentence(self, chunker):
        chunker.max_tokens_per_chunk = 10
        chunks = chunker.group_into_chunks(["A very long sentence that goes beyond the maximum chunk size."])
        assert len(chunks) > 1

    def test_preserves_all_text(self, chunker):
        sentences = ["First.", "Second.", "Third."]
        chunks = chunker.group_into_chunks(sentences)
        combined = " ".join(chunks)
        for s in sentences:
            assert s in combined

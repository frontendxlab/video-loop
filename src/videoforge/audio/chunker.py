from __future__ import annotations

import re

_ABBREVIATIONS = {"Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "Sr.", "Jr.", "St.", "vs."}


class Chunker:
    def __init__(self, max_tokens_per_chunk: int = 50):
        self.max_tokens_per_chunk = max_tokens_per_chunk

    def split_sentences(self, text: str) -> list[str]:
        if not text:
            return []

        protected = text
        for i, abbr in enumerate(_ABBREVIATIONS):
            protected = protected.replace(
                abbr, abbr.replace(".", f"\x00ABBR{i}\x00")
            )

        parts = re.split(r"(?<=[.!?])\s+", protected)

        result = []
        for part in parts:
            if not part:
                continue
            for i, abbr in enumerate(_ABBREVIATIONS):
                part = part.replace(
                    abbr.replace(".", f"\x00ABBR{i}\x00"), abbr
                )
            part = part.strip()
            if part:
                result.append(part)

        return result

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(text) // 4

    def group_into_chunks(self, sentences: list[str]) -> list[str]:
        chunks: list[str] = []
        current_chunk = ""

        for sentence in sentences:
            candidate = (
                (current_chunk + " " + sentence).strip()
                if current_chunk
                else sentence
            )

            if self.count_tokens(candidate) <= self.max_tokens_per_chunk:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                if self.count_tokens(sentence) > self.max_tokens_per_chunk:
                    sub_sentences = self._split_by_clauses(sentence)
                    sub_chunks = self._group_sub_sentences(sub_sentences)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_by_clauses(self, text: str) -> list[str]:
        parts = re.split(r"(;|,)", text)
        result: list[str] = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and parts[i + 1] in (";", ","):
                clause = (parts[i] + parts[i + 1]).strip()
                if clause:
                    result.append(clause)
                i += 2
            else:
                clause = parts[i].strip()
                if clause:
                    result.append(clause)
                i += 1
        return result

    def _group_sub_sentences(self, sub_sentences: list[str]) -> list[str]:
        chunks: list[str] = []
        current = ""

        for sub in sub_sentences:
            candidate = (current + " " + sub).strip() if current else sub

            if self.count_tokens(candidate) <= self.max_tokens_per_chunk:
                current = candidate
            else:
                if current:
                    chunks.append(current)

                if self.count_tokens(sub) > self.max_tokens_per_chunk:
                    words = sub.split()
                    word_chunks = self._group_words(words)
                    chunks.extend(word_chunks)
                    current = ""
                else:
                    current = sub

        if current:
            chunks.append(current)

        return chunks

    def _group_words(self, words: list[str]) -> list[str]:
        chunks: list[str] = []
        current = ""

        for word in words:
            candidate = (current + " " + word).strip() if current else word

            if self.count_tokens(candidate) <= self.max_tokens_per_chunk:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = word

        if current:
            chunks.append(current)

        return chunks

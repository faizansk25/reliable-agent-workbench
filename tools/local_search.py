"""Deterministic lexical retrieval for local documents."""

from __future__ import annotations

import re
from collections.abc import Mapping


def search_documents(
    query: str, documents: Mapping[str, str], max_results: int = 5
) -> list[dict[str, str | int]]:
    if max_results < 1:
        raise ValueError("max_results must be at least 1")
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    ranked: list[tuple[int, str, str]] = []
    for title, text in documents.items():
        words = set(re.findall(r"[a-z0-9]+", text.lower()))
        score = len(terms & words)
        if score:
            ranked.append((score, title, text))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [
        {"title": title, "snippet": text[:200], "score": score}
        for score, title, text in ranked[:max_results]
    ]

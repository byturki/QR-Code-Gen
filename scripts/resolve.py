"""Fuzzy-match free text (filename, folder name, or user-typed department) to
a real Azure container name."""

import difflib
import re

from containers import CONTAINERS, CONTAINER_NAMES


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def rank_candidates(text: str) -> list[tuple[str, float]]:
    """Return [(container_name, score)] sorted best-first, score in 0..1."""
    query = _normalize(text)
    if not query:
        return []

    scores: dict[str, float] = {}
    for entry in CONTAINERS:
        name = entry["name"]
        terms = [entry["name"]] + entry["aliases"]
        best = 0.0
        for term in terms:
            norm_term = _normalize(term)
            if not norm_term:
                continue
            if query == norm_term:
                score = 1.0
            elif norm_term in query or query in norm_term:
                score = 0.9
            else:
                score = difflib.SequenceMatcher(None, query, norm_term).ratio()
            best = max(best, score)
        scores[name] = best

    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def resolve_container(explicit: str | None, filename: str = "", folder: str = "",
                       threshold: float = 0.6):
    """Resolve a container name from an explicit value or inferred text.

    Returns a dict: {"resolved": name_or_None, "confidence": float,
    "candidates": [(name, score), ...], "source": "explicit"|"inferred"}
    """
    if explicit:
        norm = explicit.strip().lower()
        exact = next((n for n in CONTAINER_NAMES if n.lower() == norm), None)
        if exact:
            return {"resolved": exact, "confidence": 1.0,
                    "candidates": [(exact, 1.0)], "source": "explicit"}
        candidates = rank_candidates(explicit)
        return {"resolved": None, "confidence": candidates[0][1] if candidates else 0.0,
                "candidates": candidates[:5], "source": "explicit"}

    combined = f"{folder} {filename}"
    candidates = rank_candidates(combined)
    if candidates and candidates[0][1] >= threshold:
        return {"resolved": candidates[0][0], "confidence": candidates[0][1],
                "candidates": candidates[:5], "source": "inferred"}
    return {"resolved": None, "confidence": candidates[0][1] if candidates else 0.0,
            "candidates": candidates[:5], "source": "inferred"}

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Tuple


def _norm_text(s: str) -> str:
    s = s or ""
    s = unicodedata.normalize("NFKD", s)
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa = set(a)
    sb = set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


def tokenize_for_similarity(text: str) -> List[str]:
    t = _norm_text(text)
    # Keep alphanumerics and common puzzle markers.
    t = re.sub(r"[^a-z0-9#]+", " ", t)
    return [x for x in t.split(" ") if x]


def similarity_score(query_text: str, candidate_text: str) -> float:
    """Lightweight similarity for puzzle memory retrieval.

    Without OCR/perfect structural parsing, we use token-jaccard.
    """
    q = tokenize_for_similarity(query_text)
    c = tokenize_for_similarity(candidate_text)
    return jaccard(q, c)


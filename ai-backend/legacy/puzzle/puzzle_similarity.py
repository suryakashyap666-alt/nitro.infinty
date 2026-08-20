from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List


def _norm_text(s: str) -> str:
    s = s or ""
    s = unicodedata.normalize("NFKD", s)
    s = s.lower()
    return re.sub(r"\s+", " ", s).strip()


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa = set(a)
    sb = set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


def similarity_score(query_text: str, candidate_text: str) -> float:
    q = [x for x in re.sub(r"[^a-z0-9#]+", " ", _norm_text(query_text)).split() if x]
    c = [x for x in re.sub(r"[^a-z0-9#]+", " ", _norm_text(candidate_text)).split() if x]
    return jaccard(q, c)
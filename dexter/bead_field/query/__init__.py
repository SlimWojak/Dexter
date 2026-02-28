"""Gate 2 Query Layer — S62 Track B.

Public API:
    normalize_timestamp  — T2: canonical UTC timestamp normalization
    walk_chain          — T3: hash chain traversal with verification
    verify_bead         — T4: full integrity check (hash/chain/merkle)
    known_at            — T5: bi-temporal "what did we know at KT about WT?"
    FieldQuery          — T6: cross-pair parallel query fan-out
"""

from .timestamps import normalize_timestamp, normalize_params
from .chain import walk_chain, ChainEntry, ChainIntegrityError
from .verify import verify_bead, VerificationResult
from .temporal import known_at, BeadRecord
from .field_query import FieldQuery, FieldQueryResult, QueryResult

__all__ = [
    "normalize_timestamp",
    "normalize_params",
    "walk_chain",
    "ChainEntry",
    "ChainIntegrityError",
    "verify_bead",
    "VerificationResult",
    "known_at",
    "BeadRecord",
    "FieldQuery",
    "FieldQueryResult",
    "QueryResult",
]

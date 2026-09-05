"""Source lineage helpers."""
from __future__ import annotations

import hashlib
from collections.abc import Iterable


def source_ids_hash(source_id_column: str, source_ids: Iterable[str]) -> str:
    """Hash deterministic source IDs with the grain column as a prefix."""
    digest = hashlib.sha256()
    digest.update(f"{source_id_column}\n".encode())
    for source_id in source_ids:
        digest.update(f"{source_id}\n".encode())
    return digest.hexdigest()

from typing import Set
from src.utils.hashing import hash_url, hash_entity

class Deduplicator:
    """Provides fast in-memory bloom/set tracking to prune duplicates before DB calls."""

    def __init__(self):
        self._seen_hashes: Set[str] = set()

    def is_seen(self, identifier: str, scope: str = "") -> bool:
        h = hash_entity(identifier, scope=scope)
        if h in self._seen_hashes:
            return True
        self._seen_hashes.add(h)
        return False

    def is_url_seen(self, url: str) -> bool:
        h = hash_url(url)
        if h in self._seen_hashes:
            return True
        self._seen_hashes.add(h)
        return False

    def clear(self) -> None:
        self._seen_hashes.clear()

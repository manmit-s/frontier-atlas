from typing import Tuple, Optional
from src.entity_resolution.normalizer import normalize_entity_name
from src.entity_resolution.scoring import find_best_canonical_match
from src.llm.schemas import EntityMappingLog

class EntityResolver:
    """
    Deterministic & Fuzzy Entity Resolution Engine.
    Canonicalizes messy company and product strings.
    """

    def __init__(self):
        pass

    def resolve(self, raw_name: str, source_url: str = "") -> Tuple[str, EntityMappingLog]:
        """
        Resolves a raw entity name to its canonical form and returns the mapping log.
        """
        if not raw_name or not raw_name.strip():
            fallback = "Unknown"
            log = EntityMappingLog(
                raw_name=raw_name or "",
                canonical_name=fallback,
                method="EMPTY_FALLBACK",
                confidence=0.0,
                source_url=source_url
            )
            return fallback, log

        cleaned = raw_name.strip()
        normalized = normalize_entity_name(cleaned)

        # Attempt resolution
        canonical_cand, confidence, method = find_best_canonical_match(normalized)

        if canonical_cand:
            canonical_name = canonical_cand
        else:
            # When unresolved, produce clean title-cased representation
            canonical_name = " ".join([w.capitalize() for w in normalized.split()])
            method = "NORMALIZED_TITLECASE"
            confidence = 60.0

        log = EntityMappingLog(
            raw_name=cleaned,
            canonical_name=canonical_name,
            method=method,
            confidence=confidence,
            source_url=source_url
        )

        return canonical_name, log

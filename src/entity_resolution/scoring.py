from typing import Optional, Tuple
from rapidfuzz import fuzz, process
from src.config.settings import settings
from src.entity_resolution.aliases import ALIAS_TO_CANONICAL, CANONICAL_ENTITIES

def calculate_fuzzy_score(name_a: str, name_b: str) -> float:
    """Calculates token sort ratio similarity score (0.0 - 100.0)."""
    if not name_a or not name_b:
        return 0.0
    return float(fuzz.token_sort_ratio(name_a, name_b))

def find_best_canonical_match(
    normalized_name: str,
    confidence_threshold: float = settings.FUZZY_CONFIDENCE_THRESHOLD
) -> Tuple[Optional[str], float, str]:
    """
    Finds best matching canonical entity.
    Returns: (canonical_name, confidence, match_method)
    """
    if not normalized_name:
        return None, 0.0, "NONE"

    # Step 1: Exact alias match
    if normalized_name in ALIAS_TO_CANONICAL:
        return ALIAS_TO_CANONICAL[normalized_name], 100.0, "EXACT_ALIAS"

    # Step 2: RapidFuzz candidate search against canonical keys
    canonical_keys = list(CANONICAL_ENTITIES.keys())
    best_match = process.extractOne(
        normalized_name,
        canonical_keys,
        scorer=fuzz.token_sort_ratio
    )

    if best_match:
        matched_name, score, _ = best_match
        if score >= confidence_threshold:
            return matched_name, round(score, 1), "FUZZY_RAPIDFUZZ"

    return None, 0.0, "UNRESOLVED"

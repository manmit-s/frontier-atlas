import pytest
from src.entity_resolution.normalizer import normalize_entity_name
from src.entity_resolution.resolver import EntityResolver

def test_entity_normalization():
    assert normalize_entity_name("OpenAI, Inc.") == "openai"
    assert normalize_entity_name("Anthropic PBC") == "anthropic"
    assert normalize_entity_name("Mistral AI SAS") == "mistral ai"
    assert normalize_entity_name("Scale Labs, LLC") == "scale"

def test_exact_and_alias_resolution():
    resolver = EntityResolver()

    # OpenAI variants
    variants = ["OpenAI", "Open AI", "OpenAI, Inc.", "OpenAI Inc.", "OpenAI LLC"]
    for v in variants:
        canonical, log = resolver.resolve(v, source_url="https://test.com")
        assert canonical == "OpenAI"
        assert log.confidence >= 85.0

    # Anthropic variant
    canonical, log = resolver.resolve("Anthropic PBC", source_url="https://test.com")
    assert canonical == "Anthropic"

def test_fuzzy_matching():
    resolver = EntityResolver()
    
    # Slight typo or variation
    canonical, log = resolver.resolve("DeepMind Tech", source_url="https://test.com")
    assert canonical == "Google DeepMind"

def test_unrelated_entity_rejection():
    resolver = EntityResolver()
    
    # Unrelated entity must NOT be merged into known canonical entities
    canonical, log = resolver.resolve("Cybernetics Robotics Dynamics", source_url="https://test.com")
    assert canonical != "OpenAI"
    assert canonical != "Anthropic"
    assert log.method == "NORMALIZED_TITLECASE"

import re
import unicodedata

# Common legal and corporate entity suffixes
LEGAL_SUFFIXES = [
    r"\binc\.?\b",
    r"\bincorporated\b",
    r"\bllc\.?\b",
    r"\bltd\.?\b",
    r"\blimited\b",
    r"\bcorp\.?\b",
    r"\bcorporation\b",
    r"\bpbc\.?\b",
    r"\bgmbh\b",
    r"\bag\b",
    r"\bsas\b",
    r"\bco\.?\b",
    r"\bcompany\b",
    r"\btechnologies\b",
    r"\btechnology\b",
    r"\btech\b",
    r"\blabs\b",
    r"\bgroup\b"
]

SUFFIX_REGEX = re.compile(r"|".join(LEGAL_SUFFIXES), re.IGNORECASE)

def normalize_entity_name(raw_name: str) -> str:
    """
    Standardizes entity names:
    1. Unicode NFKD normalization
    2. Lowercase
    3. Removal of legal entity suffixes (e.g. Inc, LLC, Corp)
    4. Punctuation removal (preserving alphanumeric and essential spaces)
    5. Whitespace trimming and collapsing
    """
    if not raw_name or not isinstance(raw_name, str):
        return ""

    # Unicode normalization
    text = unicodedata.normalize("NFKD", raw_name)
    text = "".join([c for c in text if not unicodedata.combining(c)])

    # Lowercase
    text = text.lower()

    # Remove legal suffixes
    text = SUFFIX_REGEX.sub("", text)

    # Remove special punctuation (keep spaces, alphanumeric)
    text = re.sub(r"[^\w\s]", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text

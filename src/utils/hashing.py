import hashlib
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def canonicalize_url(url: str) -> str:
    """
    Normalizes a URL by converting scheme/host to lowercase,
    removing fragments, sorting query params, and stripping trailing slashes.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # Strip default ports
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        # Normalize path
        path = parsed.path
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]

        # Sort query parameters
        query_params = parse_qsl(parsed.query)
        # Filter out common tracking parameters
        tracking_params = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid"}
        filtered_params = sorted([(k, v) for k, v in query_params if k.lower() not in tracking_params])
        query = urlencode(filtered_params)

        # Rebuild URL without fragment
        clean_url = urlunparse((scheme, netloc, path, parsed.params, query, ""))
        return clean_url
    except Exception:
        return url.strip()

def hash_url(url: str) -> str:
    """Generates a deterministic SHA-256 hash of a canonicalized URL."""
    canonical = canonicalize_url(url)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def hash_entity(name: str, scope: str = "") -> str:
    """Generates a deterministic SHA-256 hash for an entity name and scope."""
    key = f"{scope}:{name.strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

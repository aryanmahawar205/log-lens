import re

class URLNormalizer:
    """
    Normalizes URLs to group dynamic endpoints.
    Replaces common ID patterns with {id}.
    """

    # Matches common ID formats in URLs (e.g., numeric, UUIDs, alphanumeric hashes)
    # Examples:
    # /user/123 -> /user/{id}
    # /product/abc-123-def -> /product/{id}
    ID_PATTERNS = [
        # Numeric ID (more than 1 digit, or single digit if surrounded by slashes/end)
        re.compile(r'(?<=/)\d+(?=/|$)'),

        # UUID
        re.compile(r'(?<=/)[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(?=/|$)'),

        # Alphanumeric long IDs (e.g., MongoDB ObjectIDs, typical hashes > 10 chars)
        re.compile(r'(?<=/)[a-zA-Z0-9_-]{10,}(?=/|$)')
    ]

    @classmethod
    def normalize(cls, url: str) -> str:
        """
        Replace ID-like segments in a URL with '{id}'.
        """
        normalized_url = url
        for pattern in cls.ID_PATTERNS:
            normalized_url = pattern.sub('{id}', normalized_url)
        return normalized_url

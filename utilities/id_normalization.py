import re


def normalize_collection_id(value):
    """Normalize collection identifiers to canonical app format.

    Example: "Rare Book" -> "rarebook"
    """
    if value is None:
        return ""

    normalized = str(value).strip().lower()
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("_")
    normalized = normalized.replace("_", "")
    return normalized

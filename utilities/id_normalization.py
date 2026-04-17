import re


def normalize_collection_id(value):
    """Normalize collection identifiers to canonical app format.

    Example: "Rare Book" -> "rare_book"
    """
    if value is None:
        return ""

    normalized = str(value).strip().lower()
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("_")
    return normalized

"""
Utility to describe document version tiers for user-facing output.
"""

from pathlib import Path

from kohlrahbi.docxfilefinder import extract_document_meta_data


def describe_version_tier(filename: str) -> str:
    """
    Return a short human-readable label describing the document version tier.

    Returns one of:
    - "error correction" (consolidated + error correction)
    - "consolidated" (consolidated, no error correction)
    - "informational" (plain informational reading version)
    - "unknown" (could not determine)
    """
    try:
        metadata = extract_document_meta_data(filename)
    except Exception:  # pylint: disable=broad-except
        return "unknown"
    if metadata is None:
        return "unknown"
    if metadata.is_consolidated_reading_version and metadata.is_error_correction:
        return "error correction"
    if metadata.is_consolidated_reading_version:
        return "consolidated"
    if metadata.is_informational_reading_version:
        return "informational"
    return "unknown"


def summarize_version_tiers(filenames: list[str]) -> str:
    """
    Given a list of filenames, return a summary of which version tiers are used.

    Example: "error correction (3), informational (12)"
    """
    tier_counts: dict[str, int] = {}
    for filename in filenames:
        tier = describe_version_tier(filename)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    # Sort by preference: error correction first, then consolidated, informational, unknown
    order = ["error correction", "consolidated", "informational", "unknown"]
    parts = []
    for tier in order:
        count = tier_counts.get(tier, 0)
        if count > 0:
            parts.append(f"{tier} ({count})")
    return ", ".join(parts)


def summarize_version_tiers_from_paths(paths: list[Path]) -> str:
    """Same as summarize_version_tiers but accepts Path objects."""
    return summarize_version_tiers([p.name for p in paths])

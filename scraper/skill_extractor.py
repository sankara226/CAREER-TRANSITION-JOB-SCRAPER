"""Extract required skills from job posting text using keyword matching
against the skills taxonomy (data/skills_taxonomy.json)."""

import re

import pandas as pd

from scraper.config import get_logger, load_skills_taxonomy

logger = get_logger(__name__)


def flatten_taxonomy(taxonomy: dict) -> dict:
    """Flatten a {category: [skills]} taxonomy into a {skill: category} lookup.

    Args:
        taxonomy: Dict mapping category name to a list of skill keywords.

    Returns:
        A dict mapping each lowercase skill keyword to its category.
    """
    flat = {}
    for category, skills in taxonomy.items():
        for skill in skills:
            flat[skill.lower()] = category
    return flat


def extract_skills(text: str, taxonomy: dict = None) -> list:
    """Find which known skills from the taxonomy appear in a piece of text.

    Uses word-boundary matching so short keywords (e.g. "r") don't match
    inside unrelated words.

    Args:
        text: Free text to search (typically a job description).
        taxonomy: Optional pre-loaded taxonomy dict; loads the default
            taxonomy from disk if not provided.

    Returns:
        A sorted list of matched skill keywords found in the text.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    taxonomy = taxonomy if taxonomy is not None else load_skills_taxonomy()
    flat_skills = flatten_taxonomy(taxonomy)
    text_lower = text.lower()

    matched = set()
    for skill in flat_skills:
        # Short tokens (e.g. "r", "c++") are prone to false positives when
        # glued to punctuation (e.g. "R&D"), so require whitespace/string-edge
        # boundaries for them instead of just "not alphanumeric".
        if len(skill) <= 2:
            boundary_before, boundary_after = r"(?:^|(?<=\s))", r"(?:$|(?=\s))"
        else:
            boundary_before, boundary_after = r"(?<![a-z0-9])", r"(?![a-z0-9])"

        pattern = boundary_before + re.escape(skill) + boundary_after
        if re.search(pattern, text_lower):
            matched.add(skill)

    return sorted(matched)


def extract_skills_from_postings(df: pd.DataFrame, text_column: str = "description",
                                  taxonomy: dict = None) -> pd.DataFrame:
    """Add a "skills" column to a job postings DataFrame by extracting
    skills from each row's description text.

    Args:
        df: DataFrame of job postings.
        text_column: Name of the column containing free-text descriptions.
        taxonomy: Optional pre-loaded taxonomy dict.

    Returns:
        A copy of df with an added "skills" column (list of matched skills
        per row). Returns df unchanged if text_column is missing.
    """
    if text_column not in df.columns:
        logger.warning("Column '%s' not found; skipping skill extraction", text_column)
        return df

    taxonomy = taxonomy if taxonomy is not None else load_skills_taxonomy()
    df = df.copy()
    df["skills"] = df[text_column].apply(lambda text: extract_skills(text, taxonomy))

    logger.info("Extracted skills for %d job posting(s)", len(df))
    return df

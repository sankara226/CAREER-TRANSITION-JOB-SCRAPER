"""Analyze extracted skills: frequency ranking, top skills by role,
and skill-gap analysis against a user's current skill set."""

from collections import Counter

import pandas as pd

from scraper.config import get_logger

logger = get_logger(__name__)


def top_skills(df: pd.DataFrame, skills_column: str = "skills", top_n: int = 20) -> pd.DataFrame:
    """Rank the most frequently requested skills across all job postings.

    Args:
        df: DataFrame with a column of per-row skill lists.
        skills_column: Name of the column containing lists of skills.
        top_n: Number of top skills to return.

    Returns:
        A DataFrame with columns ["skill", "count", "percent_of_postings"],
        sorted descending by count.
    """
    if skills_column not in df.columns or df.empty:
        logger.warning("No skills data available to rank")
        return pd.DataFrame(columns=["skill", "count", "percent_of_postings"])

    counter = Counter(skill for skills in df[skills_column] for skill in skills)
    total_postings = len(df)

    ranked = pd.DataFrame(counter.most_common(top_n), columns=["skill", "count"])
    ranked["percent_of_postings"] = (ranked["count"] / total_postings * 100).round(1)

    logger.info("Ranked top %d skill(s) across %d posting(s)", len(ranked), total_postings)
    return ranked


def top_skills_by_role(df: pd.DataFrame, role_column: str = "position",
                        skills_column: str = "skills", top_n: int = 10) -> dict:
    """Rank top skills separately for each distinct role/position title.

    Args:
        df: DataFrame with role and skills columns.
        role_column: Column identifying the job role/title.
        skills_column: Column containing lists of skills.
        top_n: Number of top skills to keep per role.

    Returns:
        A dict mapping {role: DataFrame of top skills for that role}.
    """
    if role_column not in df.columns or skills_column not in df.columns:
        logger.warning("Missing '%s' or '%s' column; cannot rank by role", role_column, skills_column)
        return {}

    results = {}
    for role, group in df.groupby(role_column):
        results[role] = top_skills(group, skills_column=skills_column, top_n=top_n)

    logger.info("Ranked top skills for %d distinct role(s)", len(results))
    return results


def skill_gap_analysis(market_skills: pd.DataFrame, current_skills: list) -> pd.DataFrame:
    """Compare in-demand market skills against a user's current skill set.

    Args:
        market_skills: DataFrame from top_skills() with a "skill" column,
            ranked by demand.
        current_skills: List of skills the user already has (case-insensitive).

    Returns:
        A copy of market_skills with an added boolean "already_have" column
        and sorted so missing high-demand skills appear first.
    """
    if market_skills.empty:
        return market_skills

    owned = {skill.lower() for skill in current_skills}
    result = market_skills.copy()
    result["already_have"] = result["skill"].str.lower().isin(owned)
    result = result.sort_values(by=["already_have", "count"], ascending=[True, False]).reset_index(drop=True)

    gap_count = int((~result["already_have"]).sum())
    logger.info("Skill gap analysis: %d missing skill(s) out of %d in-demand skill(s)",
                gap_count, len(result))
    return result

"""Generate a prioritized learning roadmap from a skill-gap analysis."""

import pandas as pd

from scraper.config import get_logger

logger = get_logger(__name__)

# Lightweight, hand-curated learning-resource pointers by taxonomy category.
LEARNING_RESOURCES = {
    "programming_languages": "Practice via project-based courses (e.g. official language docs + Exercism).",
    "data_libraries": "Hands-on notebooks (Kaggle Learn, library official tutorials).",
    "ml_ai": "Structured courses (e.g. DeepLearning.AI, fast.ai) + reproduce papers/projects.",
    "cloud_platforms": "Vendor free-tier + official certification learning paths (AWS/Azure/GCP).",
    "data_engineering": "Build an end-to-end pipeline project using the tool in a sandbox environment.",
    "visualization_bi": "Recreate dashboards from public datasets to build a portfolio.",
    "soft_skills": "Seek cross-functional project ownership and structured feedback loops.",
    "statistics": "Applied statistics course + practice designing/analyzing real experiments.",
}


def generate_learning_roadmap(gap_df: pd.DataFrame, taxonomy: dict, top_n: int = 10) -> pd.DataFrame:
    """Build a prioritized roadmap of skills to learn next.

    Args:
        gap_df: DataFrame from analyzer.skill_gap_analysis with columns
            ["skill", "count", "percent_of_postings", "already_have"].
        taxonomy: The skills taxonomy dict, used to map each skill back to
            a category so a learning-resource pointer can be attached.
        top_n: Number of missing skills to include in the roadmap.

    Returns:
        A DataFrame with columns ["priority", "skill", "demand_percent",
        "category", "suggested_resource"], ordered by demand.
    """
    if gap_df.empty:
        logger.warning("Empty skill-gap data; cannot generate roadmap")
        return pd.DataFrame(columns=["priority", "skill", "demand_percent", "category", "suggested_resource"])

    skill_to_category = {
        skill.lower(): category
        for category, skills in taxonomy.items()
        for skill in skills
    }

    missing = gap_df[~gap_df["already_have"]].head(top_n).reset_index(drop=True)
    if missing.empty:
        logger.info("No skill gaps found; user already covers top in-demand skills")
        return pd.DataFrame(columns=["priority", "skill", "demand_percent", "category", "suggested_resource"])

    roadmap = pd.DataFrame({
        "priority": range(1, len(missing) + 1),
        "skill": missing["skill"],
        "demand_percent": missing["percent_of_postings"],
    })
    roadmap["category"] = roadmap["skill"].map(lambda s: skill_to_category.get(s.lower(), "other"))
    roadmap["suggested_resource"] = roadmap["category"].map(
        lambda c: LEARNING_RESOURCES.get(c, "Search for a project-based course covering this skill.")
    )

    logger.info("Generated learning roadmap with %d skill(s)", len(roadmap))
    return roadmap

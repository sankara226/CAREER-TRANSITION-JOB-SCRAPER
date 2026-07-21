"""Generate visualizations of skill demand and save them as PNG files."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend, safe for headless/CI runs
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from scraper.config import get_logger

logger = get_logger(__name__)


def plot_top_skills(top_skills_df: pd.DataFrame, output_dir: str, top_n: int = 15) -> str:
    """Plot a horizontal bar chart of the most in-demand skills.

    Args:
        top_skills_df: DataFrame from analyzer.top_skills with "skill" and
            "count" columns.
        output_dir: Directory to save the generated PNG file into.
        top_n: Number of top skills to display.

    Returns:
        Path to the saved PNG file, or an empty string if no data is available.
    """
    if top_skills_df.empty:
        logger.warning("No skill data available; skipping top-skills plot")
        return ""

    plot_df = top_skills_df.head(top_n).sort_values("count")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, max(4, len(plot_df) * 0.4)))
    sns.barplot(data=plot_df, x="count", y="skill", ax=ax, orient="h")
    ax.set_title("Top In-Demand Skills")
    ax.set_xlabel("Number of Postings")
    ax.set_ylabel("Skill")
    fig.tight_layout()

    path = Path(output_dir) / "top_skills.png"
    fig.savefig(path)
    plt.close(fig)

    logger.info("Saved top-skills plot to %s", path)
    return str(path)


def plot_skill_gap(gap_df: pd.DataFrame, output_dir: str, top_n: int = 15) -> str:
    """Plot in-demand skills colored by whether the user already has them.

    Args:
        gap_df: DataFrame from analyzer.skill_gap_analysis with "skill",
            "count", and "already_have" columns.
        output_dir: Directory to save the generated PNG file into.
        top_n: Number of top skills to display.

    Returns:
        Path to the saved PNG file, or an empty string if no data is available.
    """
    if gap_df.empty:
        logger.warning("No gap data available; skipping skill-gap plot")
        return ""

    plot_df = gap_df.head(top_n).sort_values("count")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, max(4, len(plot_df) * 0.4)))
    sns.barplot(
        data=plot_df, x="count", y="skill", hue="already_have", dodge=False, ax=ax
    )
    ax.set_title("Skill Gap: Have vs. Missing")
    ax.set_xlabel("Number of Postings")
    ax.set_ylabel("Skill")
    ax.legend(title="Already have?")
    fig.tight_layout()

    path = Path(output_dir) / "skill_gap.png"
    fig.savefig(path)
    plt.close(fig)

    logger.info("Saved skill-gap plot to %s", path)
    return str(path)

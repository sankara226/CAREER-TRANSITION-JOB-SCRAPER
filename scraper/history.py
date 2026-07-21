"""Accumulate skill-demand results across scheduled runs so trends in
in-demand skills can be tracked over time (e.g. via a recurring
GitHub Actions job), instead of each run overwriting the last snapshot.
"""

from pathlib import Path

import pandas as pd

from scraper.config import get_logger

logger = get_logger(__name__)


def append_skill_history(top_skills_df: pd.DataFrame, run_timestamp: str,
                          query_label: str, history_path: str,
                          posting_count: int = 0) -> str:
    """Append one run's ranked skills to a growing history CSV.

    Args:
        top_skills_df: DataFrame from analyzer.top_skills with columns
            ["skill", "count", "percent_of_postings"].
        run_timestamp: ISO-format timestamp identifying this run.
        query_label: Human-readable label for the query used this run
            (e.g. "ai, data scien"), stored alongside each row for context.
        history_path: Path to the history CSV (created if missing).
        posting_count: Total number of postings analyzed this run.

    Returns:
        The history_path written to.
    """
    if top_skills_df.empty:
        logger.warning("No skill data for this run; skipping history append")
        return history_path

    run_df = top_skills_df.copy()
    run_df.insert(0, "run_timestamp", run_timestamp)
    run_df.insert(1, "query", query_label)
    run_df["posting_count"] = posting_count

    history_file = Path(history_path)
    history_file.parent.mkdir(parents=True, exist_ok=True)

    write_header = not history_file.exists()
    run_df.to_csv(history_file, mode="a", index=False, header=write_header)

    logger.info("Appended %d skill row(s) for run %s to %s",
                len(run_df), run_timestamp, history_path)
    return str(history_path)


def load_skill_history(history_path: str) -> pd.DataFrame:
    """Load the accumulated skill-demand history.

    Args:
        history_path: Path to the history CSV written by append_skill_history.

    Returns:
        The full history DataFrame, or an empty DataFrame if no history
        file exists yet.
    """
    history_file = Path(history_path)
    if not history_file.exists():
        logger.info("No history file found yet at %s", history_path)
        return pd.DataFrame()

    df = pd.read_csv(history_file)
    logger.info("Loaded %d historical row(s) from %s", len(df), history_path)
    return df

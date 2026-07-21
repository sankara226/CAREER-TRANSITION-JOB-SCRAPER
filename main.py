"""Entry point: scrape job postings for a target role, extract required
skills, analyze demand/gaps against the user's current skills, generate a
learning roadmap + summary report, and accumulate skill-demand history so
trends can be tracked across repeated/scheduled runs (see .github/workflows).

Usage:
    python main.py --query "data scientist" --current-skills python sql excel
    python main.py --query ai "data scien" --limit 100
    python main.py --input data/raw/saved_postings.csv --current-skills python
"""

import argparse
from datetime import datetime

from scraper.analyzer import skill_gap_analysis, top_skills, top_skills_by_role
from scraper.config import BASE_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, get_logger, load_skills_taxonomy
from scraper.history import append_skill_history, load_skill_history
from scraper.reporter import generate_report
from scraper.roadmap import generate_learning_roadmap
from scraper.scraper import fetch_remoteok_jobs, load_job_postings_csv
from scraper.skill_extractor import extract_skills_from_postings
from scraper.visualizer import plot_skill_demand_trend, plot_skill_gap, plot_top_skills

logger = get_logger(__name__)

HISTORY_DIR = BASE_DIR / "history"
HISTORY_CSV = HISTORY_DIR / "skill_demand_history.csv"


def run_analysis(query=None, input_csv: str = None, current_skills=None,
                  limit: int = 100, track_history: bool = True) -> dict:
    """Run the end-to-end job-scraping and skill-analysis pipeline.

    Args:
        query: Keyword or list of keywords to OR-match on RemoteOK
            (e.g. "data scientist" or ["ai", "data scien"]). Ignored if
            input_csv is provided.
        input_csv: Path to a previously saved postings CSV, used instead of
            live scraping (useful for boards that disallow scraping).
        current_skills: List of skills the user already has, for gap analysis.
        limit: Maximum number of postings to fetch when scraping live.
        track_history: Whether to append this run's results to the
            accumulating skill-demand history (history/skill_demand_history.csv).

    Returns:
        A dict with paths to the processed dataset, report, and figures, or
        an empty dict if no postings could be obtained.
    """
    current_skills = current_skills or []

    if input_csv:
        postings = load_job_postings_csv(input_csv)
    else:
        postings = fetch_remoteok_jobs(query=query, limit=limit)

    if postings.empty:
        logger.error("No job postings available; aborting analysis")
        return {}

    taxonomy = load_skills_taxonomy()
    postings = extract_skills_from_postings(postings, taxonomy=taxonomy)

    processed_path = PROCESSED_DATA_DIR / "job_postings_with_skills.csv"
    postings.to_csv(processed_path, index=False)

    ranked_skills = top_skills(postings)
    by_role = top_skills_by_role(postings)
    gap_df = skill_gap_analysis(ranked_skills, current_skills)
    roadmap_df = generate_learning_roadmap(gap_df, taxonomy)

    figures_dir = REPORTS_DIR / "figures"
    image_paths = [
        p for p in [
            plot_top_skills(ranked_skills, str(figures_dir)),
            plot_skill_gap(gap_df, str(figures_dir)),
        ] if p
    ]

    trend_image_path = ""
    run_count = 1
    if track_history:
        query_label = ", ".join(query) if isinstance(query, list) else str(query or "all")
        run_timestamp = datetime.now().isoformat(timespec="seconds")
        append_skill_history(ranked_skills, run_timestamp, query_label,
                              str(HISTORY_CSV), posting_count=len(postings))

        history_df = load_skill_history(str(HISTORY_CSV))
        run_count = history_df["run_timestamp"].nunique() if not history_df.empty else 1
        trend_image_path = plot_skill_demand_trend(history_df, str(HISTORY_DIR / "figures"))
        if trend_image_path:
            image_paths.append(trend_image_path)

    report_path = generate_report(
        ranked_skills, by_role, gap_df, roadmap_df,
        str(REPORTS_DIR / "summary_report.md"),
        trend_image_path=trend_image_path, run_count=run_count,
    )

    logger.info("Analysis run complete")
    return {
        "processed_dataset": str(processed_path),
        "report": report_path,
        "figures": image_paths,
        "history_csv": str(HISTORY_CSV) if track_history else None,
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape/parse job postings and analyze in-demand skills."
    )
    parser.add_argument(
        "--query", nargs="*", default=["ai", "data scientist", "data science"],
        help="Role keyword(s) to OR-match, e.g. --query ai 'data scientist'. Defaults to AI/data-science roles.",
    )
    parser.add_argument("--input", default=None, help="Path to a saved postings CSV instead of live scraping")
    parser.add_argument("--current-skills", nargs="*", default=[], help="Skills you already have")
    parser.add_argument("--limit", type=int, default=100, help="Max postings to fetch when scraping live")
    parser.add_argument("--no-history", action="store_true", help="Skip appending this run to the skill-demand history")
    args = parser.parse_args()

    results = run_analysis(
        query=args.query, input_csv=args.input,
        current_skills=args.current_skills, limit=args.limit,
        track_history=not args.no_history,
    )

    if results:
        print("Analysis finished successfully:")
        for key, value in results.items():
            print(f"  {key}: {value}")
    else:
        print("Analysis did not produce output. Check scraper.log for details.")


if __name__ == "__main__":
    main()

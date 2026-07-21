"""Generate a Markdown summary report: top skills, per-role breakdown,
skill gap analysis, and the learning roadmap."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from scraper.config import get_logger

logger = get_logger(__name__)


def generate_report(top_skills_df: pd.DataFrame, by_role: dict, gap_df: pd.DataFrame,
                     roadmap_df: pd.DataFrame, output_path: str,
                     title: str = "Career Transition Skill Report",
                     trend_image_path: str = "", run_count: int = 1) -> str:
    """Render a Markdown report from all analysis stages.

    Args:
        top_skills_df: DataFrame from analyzer.top_skills.
        by_role: Dict of {role: DataFrame} from analyzer.top_skills_by_role.
        gap_df: DataFrame from analyzer.skill_gap_analysis.
        roadmap_df: DataFrame from roadmap.generate_learning_roadmap.
        output_path: Where to write the .md report.
        title: Report title heading.
        trend_image_path: Optional path to a skill-demand trend PNG,
            included as a "Historical Trend" section when provided.
        run_count: Number of historical runs accumulated so far, shown for context.

    Returns:
        The output_path the report was written to.
    """
    lines = [
        f"# {title}",
        "",
        f"_Generated: {datetime.now().isoformat(timespec='seconds')}_",
        f"_Based on {run_count} accumulated run(s)_",
        "",
        "## Top Skills Across All Postings",
    ]
    lines.append(top_skills_df.to_markdown(index=False) if not top_skills_df.empty
                 else "_No skill data available._")

    lines += ["", "## Top Skills by Role"]
    if by_role:
        for role, role_df in by_role.items():
            lines.append(f"### {role}")
            lines.append(role_df.to_markdown(index=False) if not role_df.empty else "_No data._")
    else:
        lines.append("_No role-level breakdown available._")

    lines += ["", "## Skill Gap Analysis"]
    lines.append(gap_df.to_markdown(index=False) if not gap_df.empty
                 else "_No gap analysis available._")

    lines += ["", "## Suggested Learning Roadmap"]
    lines.append(roadmap_df.to_markdown(index=False) if not roadmap_df.empty
                 else "_No roadmap generated — no skill gaps detected or no data available._")

    lines += ["", "## Historical Trend"]
    if trend_image_path:
        lines.append(f"Skill demand over time (last {run_count} run(s)): `{trend_image_path}`")
    else:
        lines.append("_Not enough accumulated runs yet to plot a trend (need at least 2)._")

    report_text = "\n\n".join(lines)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report_text, encoding="utf-8")

    logger.info("Report written to %s", output_path)
    return str(output_path)

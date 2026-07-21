"""Job posting acquisition: real HTTP scraping against RemoteOK's public
job feed, plus a generic BeautifulSoup-based HTML parser for job postings
saved locally (e.g. from a board that disallows automated scraping).
"""

import re
from typing import List, Optional, Union

import pandas as pd
import requests
from bs4 import BeautifulSoup

from scraper.config import get_logger

logger = get_logger(__name__)

REMOTEOK_API_URL = "https://remoteok.com/api"
USER_AGENT = (
    "Mozilla/5.0 (compatible; CareerTransitionAnalyzer/1.0; "
    "+https://github.com/sankara226/CAREER-TRANSITION-JOB-SCRAPER)"
)


def _matches_any_keyword(text: str, keywords: List[str]) -> bool:
    """Check whether any keyword appears in text as a whole word/phrase.

    Uses word-boundary matching so short/ambiguous keywords like "ai" don't
    false-match inside unrelated words (e.g. "email", "detail", "maintain").
    """
    text_lower = text.lower()
    for keyword in keywords:
        pattern = r"(?<![a-z0-9])" + re.escape(keyword.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            return True
    return False


def fetch_remoteok_jobs(query: Optional[Union[str, List[str]]] = None,
                         limit: int = 100) -> pd.DataFrame:
    """Fetch live job postings from RemoteOK's public JSON feed.

    RemoteOK exposes an open JSON API (no auth required) intended for this
    kind of programmatic access, avoiding the ToS/anti-bot issues of
    scraping HTML from boards like LinkedIn or Indeed.

    Args:
        query: Optional keyword or list of keywords to filter postings by
            (OR-matched, case-insensitive, whole-word/phrase against
            position title and tags), e.g. "data" or ["ai", "data scien"].
            A single keyword can be passed as a plain string.
        limit: Maximum number of postings to return.

    Returns:
        A DataFrame with columns [id, position, company, description, tags,
        location, url, date], or an empty DataFrame on network/parse failure.
    """
    try:
        response = requests.get(
            REMOTEOK_API_URL, headers={"User-Agent": USER_AGENT}, timeout=15
        )
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        logger.error("Failed to fetch jobs from RemoteOK: %s", exc)
        return pd.DataFrame()
    except ValueError as exc:
        logger.error("Failed to parse RemoteOK response as JSON: %s", exc)
        return pd.DataFrame()

    # The first element of the RemoteOK feed is a legacy metadata object, not a job.
    jobs = [item for item in payload if isinstance(item, dict) and "position" in item]

    keywords = [query] if isinstance(query, str) else (query or [])
    if keywords:
        jobs = [
            job for job in jobs
            if _matches_any_keyword(str(job.get("position", "")), keywords)
            or any(_matches_any_keyword(str(tag), keywords) for tag in job.get("tags", []))
        ]

    jobs = jobs[:limit]
    if not jobs:
        logger.warning("No RemoteOK postings matched query=%r", query)
        return pd.DataFrame()

    df = pd.DataFrame([
        {
            "id": job.get("id"),
            "position": job.get("position"),
            "company": job.get("company"),
            "description": job.get("description", ""),
            "tags": ", ".join(job.get("tags", [])) if isinstance(job.get("tags"), list) else "",
            "location": job.get("location", ""),
            "url": job.get("url", ""),
            "date": job.get("date", ""),
        }
        for job in jobs
    ])

    logger.info("Fetched %d job posting(s) from RemoteOK (query=%r)", len(df), query)
    return df


def parse_job_posting_html(html: str, url: str = "") -> dict:
    """Extract a job posting's title, company, and description text from raw HTML.

    Useful for boards that prohibit automated scraping: the user can save
    a posting page's HTML locally and run it through this parser instead.
    Falls back gracefully across a few common heading/element patterns.

    Args:
        html: Raw HTML content of a job posting page.
        url: Optional source URL, stored alongside the parsed fields.

    Returns:
        A dict with keys "title", "company", "description", "url". Any
        field that can't be located defaults to an empty string.
    """
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception as exc:  # malformed HTML shouldn't crash the pipeline
        logger.error("Failed to parse job posting HTML: %s", exc)
        return {"title": "", "company": "", "description": "", "url": url}

    title_tag = soup.find(["h1", "h2"])
    title = title_tag.get_text(strip=True) if title_tag else ""

    company_tag = soup.find(attrs={"class": lambda c: c and "company" in c.lower()})
    company = company_tag.get_text(strip=True) if company_tag else ""

    description = soup.get_text(separator=" ", strip=True)

    logger.info("Parsed job posting HTML (title=%r, company=%r)", title, company)
    return {"title": title, "company": company, "description": description, "url": url}


def load_job_postings_csv(file_path: str) -> pd.DataFrame:
    """Load previously saved job postings from a CSV file.

    Args:
        file_path: Path to a CSV with at minimum a "description" column.

    Returns:
        The loaded DataFrame, or an empty DataFrame on failure.
    """
    try:
        df = pd.read_csv(file_path)
        logger.info("Loaded %d job posting(s) from %s", len(df), file_path)
        return df
    except FileNotFoundError:
        logger.error("Job postings CSV not found: %s", file_path)
    except pd.errors.ParserError as exc:
        logger.error("Could not parse job postings CSV %s: %s", file_path, exc)
    return pd.DataFrame()

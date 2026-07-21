# CAREER-TRANSITION-JOB-SCRAPER

Scrapes/parses job postings for any target role, extracts required skills,
analyzes demand trends, and produces a skill-gap analysis + learning
roadmap to support a career transition into AI/data roles (or any role).

## Problem

Understanding what skills employers actually want for a target role means
manually reading dozens of job postings — tedious and hard to keep current.

## Solution

1. **Acquire postings** (`scraper/scraper.py`):
   - `fetch_remoteok_jobs()` — real HTTP scraping via `requests` against
     [RemoteOK's public JSON job feed](https://remoteok.com/api), an open
     API intended for this kind of programmatic access (no auth, no ToS
     violation, unlike scraping HTML off LinkedIn/Indeed).
   - `parse_job_posting_html()` — a `BeautifulSoup`-based generic parser
     for job posting HTML you've saved locally, for boards that disallow
     automated scraping.
   - `load_job_postings_csv()` — load previously saved postings from CSV.
2. **Extract skills** (`scraper/skill_extractor.py`) — keyword-matches each
   posting's description against a curated skills taxonomy
   (`data/skills_taxonomy.json`) covering languages, ML/AI, cloud,
   data engineering, BI tools, statistics, and soft skills.
3. **Analyze** (`scraper/analyzer.py`) — ranks top skills overall and per
   role, then compares against the user's current skills to find gaps.
4. **Roadmap** (`scraper/roadmap.py`) — turns the skill gap into a
   prioritized, resource-linked learning plan.
5. **Visualize & report** (`scraper/visualizer.py`, `scraper/reporter.py`)
   — bar charts of skill demand/gaps and a Markdown summary report.

## Project Structure

```
CAREER-TRANSITION-JOB-SCRAPER/
├── main.py                    # CLI entry point / orchestrator
├── scraper/
│   ├── config.py              # paths, logging, taxonomy loader
│   ├── scraper.py             # RemoteOK API + BeautifulSoup HTML parser
│   ├── skill_extractor.py     # keyword-based skill extraction
│   ├── analyzer.py            # top skills, by-role ranking, gap analysis
│   ├── roadmap.py             # learning roadmap generation
│   ├── visualizer.py          # matplotlib/seaborn plots
│   └── reporter.py            # Markdown report generation
├── data/
│   ├── skills_taxonomy.json   # curated skill keyword taxonomy
│   ├── raw/                   # saved postings (CSV) for offline use
│   └── processed/             # postings enriched with extracted skills
├── reports/                   # generated report + figures
├── tests/                     # pytest unit tests
└── requirements.txt
```

## Usage

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Live scrape RemoteOK for "data scientist" postings:
python main.py --query "data scientist" --current-skills python sql excel

# Or analyze previously saved postings instead of scraping live:
python main.py --input data/raw/sample_postings.csv --current-skills python sql
```

Output:
- `data/processed/job_postings_with_skills.csv` — postings with extracted skills
- `reports/summary_report.md` — top skills, by-role breakdown, gap analysis, roadmap
- `reports/figures/*.png` — top-skills and skill-gap bar charts

## Running Tests

```bash
pip install pytest
pytest tests/
```

## Notes on scraping responsibly

Many major job boards (LinkedIn, Indeed) prohibit automated scraping in
their Terms of Service and employ anti-bot measures. This project uses
RemoteOK's public, unauthenticated JSON feed as its live data source
instead, and provides an HTML-parsing fallback for content the user has
legitimately saved themselves.

"""Central configuration, paths, logging, and the built-in skills taxonomy."""

import json
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
SKILLS_TAXONOMY_PATH = BASE_DIR / "data" / "skills_taxonomy.json"

for directory in (RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger that writes to both console and a file.

    Args:
        name: Name of the module requesting the logger, typically __name__.

    Returns:
        A logging.Logger instance with console + file handlers attached.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(BASE_DIR / "scraper.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def load_skills_taxonomy() -> dict:
    """Load the skills taxonomy used for keyword-based skill extraction.

    Returns:
        A dict mapping {category: [skill_names]}, e.g.
        {"programming_languages": ["python", "sql", ...], ...}.
        Returns an empty dict if the taxonomy file is missing/invalid.
    """
    logger = get_logger(__name__)
    try:
        with open(SKILLS_TAXONOMY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Skills taxonomy file not found: %s", SKILLS_TAXONOMY_PATH)
    except json.JSONDecodeError as exc:
        logger.error("Could not parse skills taxonomy: %s", exc)
    return {}

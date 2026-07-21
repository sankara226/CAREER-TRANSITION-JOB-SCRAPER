"""Unit tests covering skill extraction, analysis, and roadmap generation."""

import pandas as pd

from scraper.analyzer import skill_gap_analysis, top_skills, top_skills_by_role
from scraper.history import append_skill_history, load_skill_history
from scraper.roadmap import generate_learning_roadmap
from scraper.scraper import _matches_any_keyword, parse_job_posting_html
from scraper.skill_extractor import extract_skills, flatten_taxonomy

TAXONOMY = {
    "programming_languages": ["python", "sql", "r"],
    "ml_ai": ["machine learning", "nlp"],
}


def test_flatten_taxonomy():
    flat = flatten_taxonomy(TAXONOMY)
    assert flat["python"] == "programming_languages"
    assert flat["nlp"] == "ml_ai"


def test_extract_skills_matches_multiword_and_word_boundaries():
    text = "We need strong python and machine learning experience for reporting."
    matched = extract_skills(text, taxonomy=TAXONOMY)
    assert "python" in matched
    assert "machine learning" in matched
    assert "r" not in matched  # "reporting" should not match the "r" skill token


def test_extract_skills_empty_text_returns_empty_list():
    assert extract_skills("", taxonomy=TAXONOMY) == []
    assert extract_skills(None, taxonomy=TAXONOMY) == []


def test_extract_skills_short_token_ignores_punctuation_glued_acronym():
    text = "Join our R&D team to build the future."
    matched = extract_skills(text, taxonomy=TAXONOMY)
    assert "r" not in matched  # "R&D" should not match the single-letter "r" skill


def test_extract_skills_short_token_matches_standalone_mention():
    text = "Strong experience with R for statistical modeling is required."
    matched = extract_skills(text, taxonomy=TAXONOMY)
    assert "r" in matched


def test_top_skills_ranks_by_frequency():
    df = pd.DataFrame({"skills": [["python", "sql"], ["python"], ["sql", "r"]]})
    ranked = top_skills(df)
    assert ranked.iloc[0]["skill"] in {"python", "sql"}
    assert ranked.iloc[0]["count"] == 2


def test_top_skills_by_role_groups_correctly():
    df = pd.DataFrame({
        "position": ["Data Scientist", "Data Scientist", "Data Analyst"],
        "skills": [["python"], ["python", "sql"], ["excel"]],
    })
    by_role = top_skills_by_role(df)
    assert "Data Scientist" in by_role
    assert "Data Analyst" in by_role
    assert by_role["Data Scientist"].iloc[0]["skill"] == "python"


def test_skill_gap_analysis_flags_missing_skills():
    market = pd.DataFrame({"skill": ["python", "sql", "aws"], "count": [10, 8, 5],
                           "percent_of_postings": [100.0, 80.0, 50.0]})
    gap = skill_gap_analysis(market, current_skills=["python"])
    assert gap[gap["skill"] == "python"]["already_have"].iloc[0]
    assert not gap[gap["skill"] == "sql"]["already_have"].iloc[0]


def test_generate_learning_roadmap_orders_by_demand():
    gap = pd.DataFrame({
        "skill": ["sql", "aws", "python"],
        "count": [8, 5, 10],
        "percent_of_postings": [80.0, 50.0, 100.0],
        "already_have": [False, False, True],
    })
    roadmap = generate_learning_roadmap(gap, TAXONOMY, top_n=5)
    assert list(roadmap["skill"]) == ["sql", "aws"]
    assert roadmap.iloc[0]["priority"] == 1


def test_parse_job_posting_html_extracts_title():
    html = "<html><body><h1>Data Scientist</h1><p class='company-name'>Acme</p></body></html>"
    result = parse_job_posting_html(html, url="https://example.com")
    assert result["title"] == "Data Scientist"
    assert result["company"] == "Acme"
    assert result["url"] == "https://example.com"


def test_matches_any_keyword_word_boundary_avoids_false_positive():
    assert not _matches_any_keyword("Customer Email Support Specialist", ["ai"])


def test_matches_any_keyword_matches_ai_role_titles():
    keywords = ["ai", "data scientist", "data science"]
    assert _matches_any_keyword("AI Psychiatrist", keywords)
    assert _matches_any_keyword("Senior Data Scientist", keywords)
    assert not _matches_any_keyword("Customer Support Rep", keywords)


def test_append_and_load_skill_history_roundtrip(tmp_path):
    history_path = tmp_path / "history.csv"
    run1 = pd.DataFrame({"skill": ["python", "sql"], "count": [3, 2], "percent_of_postings": [75.0, 50.0]})
    run2 = pd.DataFrame({"skill": ["python"], "count": [5], "percent_of_postings": [100.0]})

    append_skill_history(run1, "2026-01-01T00:00:00", "ai, data scien", str(history_path), posting_count=4)
    append_skill_history(run2, "2026-01-02T00:00:00", "ai, data scien", str(history_path), posting_count=5)

    history = load_skill_history(str(history_path))
    assert len(history) == 3
    assert history["run_timestamp"].nunique() == 2
    assert set(history.columns) >= {"run_timestamp", "query", "skill", "count", "percent_of_postings", "posting_count"}


def test_load_skill_history_missing_file_returns_empty(tmp_path):
    assert load_skill_history(str(tmp_path / "does_not_exist.csv")).empty

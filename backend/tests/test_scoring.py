from app.scoring.matcher import JobScorer, keyword_hits


def sample_profile():
    return {
        "target_regions": ["Germany", "Europe", "Remote"],
        "target_role_families": ["RAG Engineer", "Solutions Architect", "Observability Architect"],
        "positive_keywords": ["RAG", "Elasticsearch", "observability", "customer automation", "solutions engineer"],
        "negative_keywords": ["frontline support", "US only"],
        "scoring_weights": {},
    }


def test_keyword_matching_is_case_insensitive():
    assert keyword_hits("Build RAG with Elasticsearch", ["rag", "elasticsearch"]) == ["rag", "elasticsearch"]


def test_scoring_rewards_search_observability_remote_fit():
    scorer = JobScorer(sample_profile())
    scored = scorer.score(
        {
            "title": "Observability Architect, Remote Europe",
            "description": "Advise customers on OpenTelemetry, Elasticsearch, automation, and technical strategy.",
            "location": "Remote Europe",
        },
        company_priority="high",
    )
    assert scored.final_score >= 60
    assert scored.role_family == "Observability Architect"
    assert "Elastic observability" in scored.suggested_application_angle


def test_scoring_penalizes_classic_support_and_us_only():
    scorer = JobScorer(sample_profile())
    scored = scorer.score(
        {
            "title": "Frontline Support Engineer",
            "description": "24/7 frontline support, US only.",
            "location": "United States only",
        }
    )
    assert scored.score_breakdown["support_classic_penalty"] > 0
    assert "US only" in scored.concerns

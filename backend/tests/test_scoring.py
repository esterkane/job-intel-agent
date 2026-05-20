from app.scoring.matcher import JobScorer, keyword_hits


def sample_profile():
    return {
        "search_phrases": ["AI Search Engineer", "RAG Engineer", "Knowledge Systems Engineer"],
        "keyword_groups": {
            "positive_core": ["RAG", "Elasticsearch", "retrieval", "knowledge base", "AI agents"],
            "positive_background_fit": ["observability", "customer-facing engineering", "technical advisory", "support engineering"],
            "negative": ["frontline support", "US only", "24/7"],
        },
        "scoring_weights": {},
    }


def test_keyword_matching_is_case_insensitive():
    assert keyword_hits("Build RAG with Elasticsearch", ["rag", "elasticsearch"]) == ["rag", "elasticsearch"]


def test_scoring_rewards_search_remote_fit():
    scorer = JobScorer(sample_profile())
    scored = scorer.score(
        {
            "title": "RAG Solutions Engineer, Remote Europe",
            "description": "Advise customers on Elasticsearch retrieval, knowledge base automation, and technical advisory work.",
            "location": "Remote Europe",
        },
        company_priority="high",
    )
    assert scored.final_score >= 45
    assert scored.role_family == "AI Search / RAG"
    assert "Elastic search diagnostics" in scored.suggested_application_angle


def test_scoring_penalizes_classic_support_and_us_only():
    scorer = JobScorer(sample_profile())
    scored = scorer.score(
        {
            "title": "Frontline Support Engineer",
            "description": "24/7 frontline support, US only.",
            "location": "United States only",
        }
    )
    assert scored.score_breakdown["classic_support_penalty"] > 0
    assert "remote Germany or remote EU" in scored.concerns

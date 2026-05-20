# Scoring

The default scorer is deterministic and requires no LLM.

It produces:

- `title_match_score`
- `description_match_score`
- `search_rag_score`
- `knowledge_systems_score`
- `agentic_workflow_score`
- `elastic_background_fit_score`
- `strategic_work_score`
- `remote_region_fit_score`
- `seniority_fit_score`
- `classic_support_penalty`
- `location_penalty`
- `final_score`

It also creates:

- `why_this_matches`
- `concerns`
- `suggested_application_angle`
- `suggested_cv_emphasis`

Positive and negative keywords live in `config/search_profile.yaml`. Adjust `scoring_weights` there to make the app stricter or more exploratory.

Location logic is intentionally strict: remote Germany and remote EU/EMEA are preferred, hybrid Munich/Augsburg can pass, and US-only, Canada-only, UK-only, London, Amsterdam, onsite-only, or relocation-required roles are heavily penalized or filtered out.

Semantic matching is an optional layer. When `sentence-transformers` is available, the app embeds the job title and description, compares it with `target_profile_text`, stores the job vector in PostgreSQL JSON, and blends the semantic score into the final score at a light weight. If the model cannot load, the app skips semantic ranking cleanly.

When `QDRANT_ENABLED=true`, the app also attempts to upsert vectors to a `jobs` collection in Qdrant. Qdrant is still optional; failures there do not stop ingestion.

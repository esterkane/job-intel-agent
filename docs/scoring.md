# Scoring

The default scorer is deterministic and requires no LLM.

It produces:

- `role_title_score`
- `description_score`
- `remote_fit_score`
- `region_fit_score`
- `company_fit_score`
- `seniority_fit_score`
- `support_classic_penalty`
- `strategic_work_score`
- `ai_search_relevance_score`
- `knowledge_kcs_score`
- `final_score`

It also creates:

- `why_this_matches`
- `concerns`
- `suggested_application_angle`
- `suggested_cv_emphasis`

Positive and negative keywords live in `config/profile.yaml`. Adjust `scoring_weights` there to make the app stricter or more exploratory.

Semantic matching is an optional layer. When `sentence-transformers` is available, the app embeds the job title and description, compares it with `target_profile_text`, stores the job vector in PostgreSQL JSON, and blends the semantic score into the final score at a light weight. If the model cannot load, the app skips semantic ranking cleanly.

When `QDRANT_ENABLED=true`, the app also attempts to upsert vectors to a `jobs` collection in Qdrant. Qdrant is still optional; failures there do not stop ingestion.

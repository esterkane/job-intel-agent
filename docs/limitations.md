# Limitations

- Career pages change often. Generic adapters are useful for discovery but source-specific adapters will be more reliable.
- Some sources may block automated browsers or require explicit API/ATS integration.
- The app does not bypass CAPTCHAs, login walls, or anti-bot systems.
- JobSpy is optional and should be used carefully with platform terms and rate limits in mind.
- Semantic ranking and local LLM summaries are optional layers, not required MVP functionality.
- `PUT /api/profile` is a placeholder in this MVP. Edit `config/profile.yaml` directly.
- Missing-job expiry is represented in the data model but not fully automated yet.
- Alembic migrations are not included in the MVP; SQLAlchemy creates tables at startup. Add Alembic before multi-user or long-lived production use.

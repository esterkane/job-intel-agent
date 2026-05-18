# Sources

Sources are configured in `config/sources.yaml`.

Each source includes:

- `company_name`
- `career_url`
- `source_type`
- `adapter_type`
- `remote_policy_notes`
- `culture_notes`
- `priority`
- `include_keywords`
- `exclude_keywords`
- `target_regions`
- `enabled`

Adapters:

- `static_html`: uses `httpx` and BeautifulSoup for simple pages.
- `generic_playwright`: opens JavaScript-heavy pages with Playwright and extracts visible links/cards.
- `jobspy`: optional and documented as rate-limit sensitive.
- `greenhouse`, `lever`, `ashby`, `workable`, `smartrecruiters`: placeholders/fallbacks for ATS-specific hardening.

LinkedIn is included only as a manual reference and is disabled by default.

The initial enabled set is small on purpose. Enable more sources after checking site terms and adapter behavior.

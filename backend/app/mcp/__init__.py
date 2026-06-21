"""Read-only MCP layer for job-intel-agent.

Exposes the existing job-intelligence core (job listing/filtering, get-job-by-id,
and the configured-source catalog) as MCP tools so an agent — Claude Code,
Cursor, a LangGraph client — can query job intelligence without HTTP.

These are *thin* adapters: all logic lives in the existing query helpers,
services, and the deterministic ``JobScorer``. The MCP layer adds no business
logic and is strictly read-only — scrape-run / ingest / manual-capture and any
other mutation are intentionally NOT exposed as tools.
"""

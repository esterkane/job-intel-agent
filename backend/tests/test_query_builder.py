from app.search.query_builder import (
    GERMAN_QUERY_PHRASES,
    MANUAL_ONLY_PLATFORMS,
    NEGATIVE_KEYWORDS,
    TARGET_ROLE_FAMILIES,
    build_search_strategy,
)


def test_query_generation_includes_all_target_role_families():
    role_families = {item["role_family"] for item in build_search_strategy()}
    assert set(TARGET_ROLE_FAMILIES).issubset(role_families)


def test_negative_keywords_are_included_where_supported():
    queries = build_search_strategy()
    supported = [item for item in queries if item["negative_keywords"]]
    assert supported
    for keyword in NEGATIVE_KEYWORDS:
        assert any(keyword in item["negative_keywords"] for item in supported)
    assert any("NOT" in item["query"] for item in supported)


def test_restricted_platforms_are_manual_only():
    queries = build_search_strategy()
    for platform in MANUAL_ONLY_PLATFORMS:
        platform_queries = [item for item in queries if item["platform"] == platform]
        assert platform_queries
        assert {item["mode"] for item in platform_queries} == {"manual_only"}
        assert all(item["url"] for item in platform_queries)


def test_api_platforms_are_filter_locally():
    queries = build_search_strategy()
    modes = {item["platform"]: item["mode"] for item in queries if item["platform"] in {"Arbeitnow", "Working Nomads"}}
    assert modes == {"Arbeitnow": "api_filter_locally", "Working Nomads": "api_filter_locally"}


def test_german_and_english_variants_are_generated():
    queries = build_search_strategy()
    languages = {item["language"] for item in queries}
    assert {"German", "English"}.issubset(languages)
    assert any(item["query_name"] in GERMAN_QUERY_PHRASES for item in queries)

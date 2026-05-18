from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


def normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").lower()).strip()


def keyword_hits(text: str, keywords: list[str]) -> list[str]:
    normalized = normalize_text(text)
    return [kw for kw in keywords if normalize_text(kw) in normalized]


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


@dataclass
class ScoredJob:
    final_score: float
    role_family: str
    score_breakdown: dict[str, float]
    why_this_matches: str
    concerns: str
    suggested_application_angle: str
    suggested_cv_emphasis: str


class JobScorer:
    def __init__(self, profile: dict[str, Any]):
        self.profile = profile
        self.positive = profile.get("positive_keywords", [])
        self.negative = profile.get("negative_keywords", [])
        self.role_families = profile.get("target_role_families", [])
        self.regions = profile.get("target_regions", ["Germany", "EU", "Europe", "Remote", "Work from anywhere", "CET", "CEST"])
        self.weights = profile.get("scoring_weights", {})

    def score(self, job: dict[str, Any], company_priority: str = "medium") -> ScoredJob:
        title = job.get("title") or ""
        description = job.get("description") or ""
        location = job.get("location") or ""
        combined = f"{title} {description} {location}"

        title_hits = keyword_hits(title, self.positive + self.role_families)
        desc_hits = keyword_hits(description, self.positive)
        neg_hits = keyword_hits(combined, self.negative)
        role_family = self._role_family(title, description)

        role_title_score = clamp(len(title_hits) * 18 + (35 if role_family else 0))
        description_score = clamp(len(desc_hits) * 6)
        remote_fit_score = self._remote_score(combined)
        region_fit_score = self._region_score(location, description)
        company_fit_score = {"high": 90, "medium": 65, "low": 45}.get(company_priority, 65)
        seniority_fit_score = self._seniority_score(title)
        support_classic_penalty = clamp(len(neg_hits) * 12)
        strategic_work_score = clamp(len(keyword_hits(combined, [
            "strategy", "advisory", "automation", "enablement", "architecture",
            "customer success", "solutions", "developer education", "knowledge",
        ])) * 12)
        ai_search_relevance_score = clamp(len(keyword_hits(combined, [
            "ai", "agent", "rag", "retrieval", "search", "semantic", "vector",
            "llm", "embedding", "elasticsearch", "observability", "opentelemetry",
        ])) * 10)
        knowledge_kcs_score = clamp(len(keyword_hits(combined, [
            "knowledge", "kcs", "enablement", "docs", "learning", "education", "support operations",
        ])) * 14)

        breakdown = {
            "role_title_score": role_title_score,
            "description_score": description_score,
            "remote_fit_score": remote_fit_score,
            "region_fit_score": region_fit_score,
            "company_fit_score": company_fit_score,
            "seniority_fit_score": seniority_fit_score,
            "support_classic_penalty": support_classic_penalty,
            "strategic_work_score": strategic_work_score,
            "ai_search_relevance_score": ai_search_relevance_score,
            "knowledge_kcs_score": knowledge_kcs_score,
        }
        weighted = (
            role_title_score * self.weights.get("role_title_score", 0.18)
            + description_score * self.weights.get("description_score", 0.16)
            + remote_fit_score * self.weights.get("remote_fit_score", 0.14)
            + region_fit_score * self.weights.get("region_fit_score", 0.12)
            + company_fit_score * self.weights.get("company_fit_score", 0.08)
            + seniority_fit_score * self.weights.get("seniority_fit_score", 0.08)
            + strategic_work_score * self.weights.get("strategic_work_score", 0.12)
            + ai_search_relevance_score * self.weights.get("ai_search_relevance_score", 0.08)
            + knowledge_kcs_score * self.weights.get("knowledge_kcs_score", 0.04)
            - support_classic_penalty * self.weights.get("support_classic_penalty", 0.14)
        )
        final_score = round(clamp(weighted), 1)

        return ScoredJob(
            final_score=final_score,
            role_family=role_family or "Strategic technical role",
            score_breakdown=breakdown,
            why_this_matches=self._why(role_family, title_hits, desc_hits),
            concerns=self._concerns(neg_hits, remote_fit_score, region_fit_score),
            suggested_application_angle=self._angle(role_family, combined),
            suggested_cv_emphasis=self._cv_emphasis(combined),
        )

    def _role_family(self, title: str, description: str) -> str:
        combined = f"{title} {description}"
        hits = keyword_hits(combined, self.role_families)
        if hits:
            return hits[0]
        if keyword_hits(combined, ["rag", "retrieval", "vector search", "semantic search"]):
            return "RAG Engineer"
        if keyword_hits(combined, ["solutions engineer", "solutions architect", "customer engineer"]):
            return "Solutions Engineer"
        if keyword_hits(combined, ["enablement", "education", "developer advocate", "docs"]):
            return "Developer Education / Enablement"
        if keyword_hits(combined, ["observability", "opentelemetry", "apm"]):
            return "Observability Architect"
        return ""

    def _remote_score(self, text: str) -> float:
        normalized = normalize_text(text)
        if any(term in normalized for term in ["onsite only", "office-based", "office based", "must be onsite"]):
            return 5
        if any(term in normalized for term in ["work from anywhere", "remote worldwide", "anywhere", "global remote", "fully remote"]):
            return 100
        if any(term in normalized for term in ["remote", "distributed", "remote-first", "remote first"]):
            return 95
        if "hybrid" in normalized:
            return 55
        return 35

    def _region_score(self, location: str, description: str) -> float:
        text = normalize_text(f"{location} {description}")
        blocking_regions = [
            "us only", "united states only", "u.s. only", "usa only", "remote united states", "united states (remote)", "north america only",
            "americas only", "must be based in the us", "pst hours only", "est hours only",
            "pacific time only", "eastern time only", "remote canada", "remote japan", "remote australia", "remote singapore",
        ]
        if any(term in text for term in blocking_regions):
            return 0
        if self._is_work_from_anywhere(text):
            return 100
        if self._is_remote_germany_or_europe(text):
            return 95
        if "remote" in text:
            return 20
        return 25

    def _is_work_from_anywhere(self, text: str) -> bool:
        return any(term in text for term in [
            "work from anywhere", "remote worldwide", "anywhere in the world", "global remote",
            "work anywhere", "fully remote worldwide", "remote - worldwide", "remote anywhere",
        ])

    def _is_remote_germany_or_europe(self, text: str) -> bool:
        exact_remote_region_terms = [
            "remote germany", "germany remote", "germany (remote)", "remote deutschland",
            "remote europe", "europe remote", "europe (remote)", "remote - europe", "remote, europe",
            "remote emea", "emea remote", "emea (remote)", "remote - emea", "remote, emea",
            "remote eu", "eu remote", "eu (remote)", "remote - eu", "remote, eu",
            "remote cet", "cet remote", "remote cest", "cest remote", "central european remote",
            "remote utc+0", "remote utc +0", "remote utc+1", "remote utc +1", "remote utc+2",
            "remote utc +2", "remote utc+3", "remote utc +3", "remote gmt+0", "remote gmt +0",
            "remote gmt+1", "remote gmt +1", "remote gmt+2", "remote gmt +2", "remote gmt+3",
            "remote gmt +3",
        ]
        return any(term in text for term in exact_remote_region_terms)

    def _seniority_score(self, title: str) -> float:
        text = normalize_text(title)
        if "principal software engineer" in text or "staff software engineer" in text:
            return 20
        if "senior" in text or "lead" in text or "architect" in text:
            return 85
        if "manager" in text or "specialist" in text or "engineer" in text:
            return 75
        return 55

    def _why(self, role_family: str, title_hits: list[str], desc_hits: list[str]) -> str:
        hits = ", ".join(dict.fromkeys(title_hits + desc_hits[:6]))
        base = f"Strong fit for {role_family or 'a strategic technical path'}"
        if hits:
            base += f" because it mentions {hits}."
        else:
            base += " based on title, remote fit, and company/source priority."
        return base

    def _concerns(self, neg_hits: list[str], remote_score: float, region_score: float) -> str:
        concerns: list[str] = []
        if neg_hits:
            concerns.append("Potential mismatch keywords: " + ", ".join(neg_hits[:6]) + ".")
        if remote_score < 60:
            concerns.append("Remote policy needs manual confirmation.")
        if region_score < 60:
            concerns.append("Location must explicitly allow remote Germany, remote Europe/EMEA, or true work-from-anywhere.")
        return " ".join(concerns) or "No obvious concern from deterministic matching."

    def _angle(self, role_family: str, text: str) -> str:
        if keyword_hits(text, ["grafana", "observability", "opentelemetry", "apm"]):
            return "Lead with Elastic observability diagnostics, customer advisory work, and production troubleshooting judgment."
        if keyword_hits(text, ["langchain", "rag", "retrieval", "agent"]):
            return "Frame your Elastic search background as the practical grounding for RAG, agentic workflows, and customer-facing AI implementation."
        if keyword_hits(text, ["knowledge", "kcs", "enablement", "docs", "education"]):
            return "Position support engineering experience as evidence you can modernize knowledge workflows and teach complex systems clearly."
        return f"Connect your Elastic support engineering background to {role_family or 'strategic customer-facing technical work'}, and explicitly position yourself as effective in remote, async, Germany/CET-friendly teams."

    def _cv_emphasis(self, text: str) -> str:
        areas = ["Elasticsearch/search diagnostics", "customer-facing technical advisory", "support automation and tooling"]
        if keyword_hits(text, ["ai", "rag", "llm", "agent"]):
            areas.append("AI/RAG learning projects and local-first experimentation")
        if keyword_hits(text, ["observability", "apm", "opentelemetry"]):
            areas.append("Observability/APM troubleshooting")
        if keyword_hits(text, ["knowledge", "docs", "enablement", "kcs"]):
            areas.append("KCS, knowledge base, and enablement thinking")
        return "; ".join(areas) + "."

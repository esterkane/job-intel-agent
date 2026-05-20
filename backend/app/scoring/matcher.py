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
        groups = profile.get("keyword_groups", {})
        self.search_phrases = profile.get("search_phrases", [])
        self.positive_core = groups.get("positive_core", profile.get("positive_keywords", []))
        self.background = groups.get("positive_background_fit", [])
        self.negative = groups.get("negative", profile.get("negative_keywords", []))
        self.weights = profile.get("scoring_weights", {})

    def score(self, job: dict[str, Any], company_priority: str = "medium") -> ScoredJob:
        title = job.get("title") or ""
        description = job.get("description") or ""
        location = job.get("location") or ""
        remote_type = job.get("remote_type") or ""
        combined = f"{title} {description} {location} {remote_type}"

        title_match_score = clamp(len(keyword_hits(title, self.search_phrases + self.positive_core)) * 16)
        description_match_score = clamp(len(keyword_hits(description, self.positive_core + self.background)) * 5)
        search_rag_score = clamp(len(keyword_hits(combined, [
            "rag", "retrieval", "vector search", "semantic search", "hybrid search", "elasticsearch",
            "opensearch", "lucene", "embeddings", "reranking", "search relevance",
        ])) * 13)
        knowledge_systems_score = clamp(len(keyword_hits(combined, [
            "knowledge systems", "knowledge platform", "knowledge base", "kcs", "knowledge operations",
            "documentation", "document intelligence", "document processing",
        ])) * 15)
        agentic_workflow_score = clamp(len(keyword_hits(combined, [
            "agentic workflow", "ai agents", "agents", "workflow automation", "ai workflow",
            "support automation", "customer automation",
        ])) * 14)
        elastic_background_fit_score = clamp(len(keyword_hits(combined, self.background)) * 7)
        strategic_work_score = clamp(len(keyword_hits(combined, [
            "solutions engineer", "solutions architect", "forward deployed", "technical advisory",
            "customer advisory", "enablement", "developer advocate", "technical writer",
            "automation engineer", "platform engineer",
        ])) * 12)
        remote_region_fit_score, location_penalty = self._location_scores(combined)
        seniority_fit_score = self._seniority_score(title, combined)
        classic_support_penalty = clamp(len(keyword_hits(combined, self.negative)) * 14)

        breakdown = {
            "title_match_score": title_match_score,
            "description_match_score": description_match_score,
            "search_rag_score": search_rag_score,
            "knowledge_systems_score": knowledge_systems_score,
            "agentic_workflow_score": agentic_workflow_score,
            "elastic_background_fit_score": elastic_background_fit_score,
            "strategic_work_score": strategic_work_score,
            "remote_region_fit_score": remote_region_fit_score,
            "seniority_fit_score": seniority_fit_score,
            "classic_support_penalty": classic_support_penalty,
            "location_penalty": location_penalty,
        }
        weighted = (
            title_match_score * self.weights.get("title_match_score", 0.15)
            + description_match_score * self.weights.get("description_match_score", 0.12)
            + search_rag_score * self.weights.get("search_rag_score", 0.14)
            + knowledge_systems_score * self.weights.get("knowledge_systems_score", 0.10)
            + agentic_workflow_score * self.weights.get("agentic_workflow_score", 0.10)
            + elastic_background_fit_score * self.weights.get("elastic_background_fit_score", 0.10)
            + strategic_work_score * self.weights.get("strategic_work_score", 0.10)
            + remote_region_fit_score * self.weights.get("remote_region_fit_score", 0.14)
            + seniority_fit_score * self.weights.get("seniority_fit_score", 0.08)
            - classic_support_penalty * self.weights.get("classic_support_penalty", 0.10)
            - location_penalty * self.weights.get("location_penalty", 0.18)
        )
        final_score = round(clamp(weighted * 1.5), 1)
        role_family = self._role_family(combined)

        return ScoredJob(
            final_score=final_score,
            role_family=role_family,
            score_breakdown=breakdown,
            why_this_matches=self._why(role_family, combined),
            concerns=self._concerns(combined, classic_support_penalty, location_penalty),
            suggested_application_angle=self._angle(role_family, combined),
            suggested_cv_emphasis=self._cv_emphasis(combined),
        )

    def _location_scores(self, text: str) -> tuple[float, float]:
        normalized = normalize_text(text)
        hard_blocks = [
            "us only", "united states only", "remote united states", "united states (remote)",
            "canada only", "remote canada", "uk only", "remote united kingdom", "london",
            "amsterdam", "onsite only", "requires relocation", "security clearance required",
        ]
        if any(term in normalized for term in hard_blocks):
            return 0, 100
        if any(term in normalized for term in ["remote germany", "germany (remote)", "germany remote", "remote deutschland"]):
            return 100, 0
        if any(term in normalized for term in [
            "remote eu", "eu remote", "remote europe", "europe remote", "remote emea", "emea remote",
            "remote cet", "remote cest", "utc+1", "utc+2", "gmt+1", "gmt+2",
        ]):
            return 95, 0
        if "hybrid" in normalized and any(city in normalized for city in ["munich", "augsburg", "muenchen", "münchen"]):
            return 70, 10
        if any(term in normalized for term in ["work from anywhere", "remote worldwide", "global remote", "remote anywhere"]):
            germany_allowed = any(term in normalized for term in ["germany", "europe", "eu", "emea", "cet", "cest"])
            return (90, 0) if germany_allowed else (45, 30)
        if "remote" in normalized:
            return 30, 45
        return 15, 55

    def _seniority_score(self, title: str, text: str) -> float:
        normalized = normalize_text(f"{title} {text}")
        if any(term in normalized for term in ["principal engineer only", "8+ years backend only"]):
            return 15
        if any(term in normalized for term in ["senior", "lead", "staff", "architect"]):
            return 80
        if any(term in normalized for term in ["engineer", "specialist", "manager", "consultant"]):
            return 75
        return 55

    def _role_family(self, text: str) -> str:
        if keyword_hits(text, ["rag", "retrieval", "vector search", "semantic search", "search backend", "search relevance"]):
            return "AI Search / RAG"
        if keyword_hits(text, ["knowledge systems", "knowledge platform", "kcs", "knowledge operations", "knowledge base"]):
            return "Knowledge Systems"
        if keyword_hits(text, ["agentic workflow", "ai agents", "agent", "ai workflow"]):
            return "Agentic Workflow"
        if keyword_hits(text, ["support automation", "support workflow", "customer automation"]):
            return "Support Automation"
        if keyword_hits(text, ["solutions engineer", "solutions architect", "forward deployed", "technical advisory"]):
            return "Solutions / Technical Advisory"
        if keyword_hits(text, ["developer advocate", "technical writer", "documentation", "enablement"]):
            return "Developer Education / Docs"
        return "Strategic AI/Search role"

    def _why(self, role_family: str, text: str) -> str:
        hits = keyword_hits(text, self.positive_core + self.background)[:8]
        if hits:
            return f"Matches the {role_family} path through: {', '.join(dict.fromkeys(hits))}."
        return f"Potential {role_family} fit based on title, strategic scope, and source metadata."

    def _concerns(self, text: str, support_penalty: float, location_penalty: float) -> str:
        concerns: list[str] = []
        neg = keyword_hits(text, self.negative)
        if neg:
            concerns.append("Mismatch keywords found: " + ", ".join(neg[:6]) + ".")
        if support_penalty:
            concerns.append("Check that this is not classic reactive/frontline support.")
        if location_penalty >= 45:
            concerns.append("Only proceed if the posting explicitly allows remote Germany or remote EU/EMEA.")
        return " ".join(concerns) or "No obvious deterministic concern."

    def _angle(self, role_family: str, text: str) -> str:
        if role_family == "AI Search / RAG":
            return "Lead with Elastic search diagnostics, relevance intuition, RAG/search learning, and customer-facing production troubleshooting."
        if role_family == "Knowledge Systems":
            return "Position support engineering plus KCS/knowledge workflow thinking as the bridge between messy customer issues and reusable systems."
        if role_family == "Agentic Workflow":
            return "Frame your support automation and AI learning projects as practical agentic workflow design for real customer operations."
        if role_family == "Solutions / Technical Advisory":
            return "Emphasize advisory judgment, stakeholder communication, and deep Elastic troubleshooting across complex production cases."
        return "Connect Elastic support engineering to strategic automation, AI search, documentation-heavy systems, and Germany/EU remote collaboration."

    def _cv_emphasis(self, text: str) -> str:
        areas = ["Elastic/Elasticsearch troubleshooting", "customer-facing technical advisory", "support diagnostics"]
        if keyword_hits(text, ["rag", "retrieval", "search", "embedding", "vector"]):
            areas.append("search/RAG projects and semantic retrieval concepts")
        if keyword_hits(text, ["knowledge", "kcs", "documentation", "enablement"]):
            areas.append("knowledge systems, documentation, and KCS thinking")
        if keyword_hits(text, ["agent", "automation", "workflow"]):
            areas.append("support automation and agentic workflow experimentation")
        return "; ".join(areas) + "."

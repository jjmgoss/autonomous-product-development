from __future__ import annotations

from typing import TypedDict


class SampleResearchBrief(TypedDict, total=False):
    title: str
    research_question: str
    constraints: str
    desired_depth: str
    expected_outputs: str
    notes: str


_SAMPLE_RESEARCH_BRIEFS: list[SampleResearchBrief] = [
    {
        "title": "Self-hosted maintenance tools for solo developers",
        "research_question": "Investigate product opportunities for solo developers who self-host small apps and struggle with deployment, monitoring, backups, and maintenance.",
        "constraints": "Focus on solo operators and very small teams. Exclude enterprise platform tooling.",
        "desired_depth": "Thorough with candidate wedges, substitutes, and validation gates.",
    },
    {
        "title": "Personal knowledge base for scattered files and notes",
        "research_question": "Investigate product opportunities for people trying to organize scattered personal notes, emails, and documents into an AI-queryable knowledge base.",
        "expected_outputs": "At least 3 candidate product wedges, likely user workflows, and evidence-backed risks.",
    },
    {
        "title": "AI research quality tools for small product teams",
        "research_question": "Investigate product opportunities for small product teams who use AI for research but struggle to distinguish useful insight from plausible slop.",
        "notes": "Look for review workflows, auditability, traceability, and confidence calibration.",
    },
    {
        "title": "Home appliance maintenance visibility",
        "research_question": "Investigate product opportunities for homeowners who want better visibility into appliance maintenance, warranties, repairs, and replacement timing.",
    },
    {
        "title": "Project memory for hobbyist builders",
        "research_question": "Investigate product opportunities for hobbyists who want to track recurring project ideas, research notes, and build artifacts across many experiments.",
    },
    {
        "title": "Semantic layer trust workflows for small data teams",
        "research_question": "Investigate product opportunities for small data teams who need to validate semantic layers and natural-language analytics before trusting AI-generated answers.",
        "constraints": "Prioritize workflow validation and explainability over pure dashboarding.",
    },
    {
        "title": "After-tax fixed-income comparison tools",
        "research_question": "Investigate product opportunities for people comparing taxable bond funds, municipal bonds, and after-tax yield tradeoffs in taxable accounts.",
        "notes": "Stay product-oriented and focus on decision-support workflows, not investment advice.",
    },
    {
        "title": "Minor-accident repair and claims coordination",
        "research_question": "Investigate product opportunities for car owners handling repair estimates, insurance claims, and certified-shop requirements after minor accidents.",
    },
    {
        "title": "Contractor CRM for tiny home-service shops",
        "research_question": "Investigate product opportunities for very small home-service businesses that juggle quotes, scheduling, customer follow-up, and unpaid invoices across text messages and spreadsheets.",
    },
    {
        "title": "Repairable-device ownership tracking",
        "research_question": "Investigate product opportunities for consumers trying to manage electronics warranties, repair history, replacement timing, and resale value across many devices.",
    },
]


def get_sample_research_briefs() -> list[SampleResearchBrief]:
    return [dict(sample) for sample in _SAMPLE_RESEARCH_BRIEFS]

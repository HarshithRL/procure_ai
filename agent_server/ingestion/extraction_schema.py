"""Extraction schema for LLM-based entity recognition from procurement documents.

Defines the structure of what the LLM should extract from each chunk:
- Vendors (suppliers, their org details, locations, certifications)
- Requirements (buyer needs, specs, performance metrics)
- Offerings (vendor proposals, prices, terms, support)
- Findings (risks, gaps, opportunities, negotiation points)

Uses Pydantic for validation and LangChain's structured output.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VendorExtract(BaseModel):
    """A vendor entity extracted from document."""
    name: str = Field(..., description="Vendor name (e.g., 'Acme Corp', 'TechSupply Inc')")
    domain: Optional[str] = Field(None, description="Business domain (e.g., 'Software', 'Hardware', 'Consulting')")
    location: Optional[str] = Field(None, description="Headquarters or primary location (e.g., 'San Francisco, CA')")
    certifications: list[str] = Field(default_factory=list, description="List of certifications (e.g., ['ISO 9001', 'SOC2'])")
    quality_summary: Optional[str] = Field(None, description="Brief quality claim or metric mentioned (e.g., '99.99% uptime', 'Zero-defect track record')")
    evidence_snippet: str = Field(..., description="Direct quote or text snippet supporting this entity")


class RequirementExtract(BaseModel):
    """A buyer requirement extracted from document."""
    title: str = Field(..., description="Short title of the requirement (e.g., 'Response Time', 'Disaster Recovery')")
    description: Optional[str] = Field(None, description="Detailed description of what is required")
    category: str = Field(default="functional", description="Category: 'functional', 'technical', 'commercial', 'compliance', 'support'")
    measurable: bool = Field(default=False, description="Whether the requirement is quantifiable (e.g., '<100ms', '>95% availability')")
    metric: Optional[str] = Field(None, description="If measurable, the quantitative metric (e.g., '24/7', '<48h', '>99.5%')")
    evidence_snippet: str = Field(..., description="Direct quote or text snippet from the document")


class PriceTermExtract(BaseModel):
    """A pricing or commercial term extracted from an offering."""
    offering_vendor: str = Field(..., description="Name of the vendor making this offer")
    article_or_component: Optional[str] = Field(None, description="What is being priced (e.g., 'Enterprise License', 'Support Package')")
    quantity: Optional[str] = Field(None, description="Unit of measurement (e.g., '1 license', '100 units', 'per month')")
    unit_price: Optional[float] = Field(None, description="Unit price (numeric only, no currency symbol)")
    currency: Optional[str] = Field(None, description="Currency code (e.g., 'USD', 'EUR')")
    total_cost: Optional[float] = Field(None, description="Total cost if stated (e.g., 10000 for 10 * 1000)")
    payment_terms: Optional[str] = Field(None, description="Payment conditions (e.g., 'Net 30', 'Monthly subscription', 'One-time')")
    discount_info: Optional[str] = Field(None, description="Any discount or volume pricing mentioned")
    evidence_snippet: str = Field(..., description="Direct quote or cell reference")


class OfferingExtract(BaseModel):
    """A vendor's proposal/bid extracted from document."""
    vendor_name: str = Field(..., description="Name of the vendor making the offer")
    offering_title: Optional[str] = Field(None, description="Name or title of the offering (e.g., 'Standard Plan', 'Enterprise Package')")
    overview: Optional[str] = Field(None, description="Brief summary of what the vendor proposes")
    delivery_timeline: Optional[str] = Field(None, description="When the vendor can deliver (e.g., '30 days', '4-6 weeks')")
    support_model: Optional[str] = Field(None, description="Support provided (e.g., '24/7 onsite', 'email support', 'dedicated account manager')")
    evidence_snippet: str = Field(..., description="Text or section header from the offering")


class FindingExtract(BaseModel):
    """A finding or insight extracted from the document."""
    finding_type: str = Field(..., description="Type: 'risk', 'gap', 'opportunity', 'negotiation_point', 'best_practice', 'concern'")
    title: str = Field(..., description="Short title of the finding (e.g., 'High delivery risk', 'Cost-saving lever')")
    description: str = Field(..., description="Detailed explanation")
    related_vendors: list[str] = Field(default_factory=list, description="Vendor names mentioned (empty if finding is general)")
    related_requirements: list[str] = Field(default_factory=list, description="Requirement names or titles mentioned")
    severity: Optional[str] = Field(None, description="For risks: 'critical', 'high', 'medium', 'low'; for opportunities: 'high_value', 'medium_value', 'low_value'")
    evidence_snippet: str = Field(..., description="Supporting text")


class ChunkExtractionResult(BaseModel):
    """The complete extraction result for one chunk of text."""
    chunk_id: Optional[str] = Field(None, description="Identifier of the chunk being processed")
    vendors: list[VendorExtract] = Field(default_factory=list, description="Vendors mentioned in this chunk")
    requirements: list[RequirementExtract] = Field(default_factory=list, description="Buyer requirements in this chunk")
    offerings: list[OfferingExtract] = Field(default_factory=list, description="Vendor offerings/proposals in this chunk")
    prices: list[PriceTermExtract] = Field(default_factory=list, description="Pricing/terms extracted")
    findings: list[FindingExtract] = Field(default_factory=list, description="Insights, risks, gaps")
    confidence_score: float = Field(default=0.8, description="LLM confidence in extraction (0-1)")
    extraction_notes: Optional[str] = Field(None, description="Any notes or warnings about extraction (e.g., ambiguous entities, conflicting info)")


# Extraction prompt for Claude
EXTRACTION_SYSTEM_PROMPT = """You are an expert procurement analyst specializing in vendor comparison and RFQ analysis.

Your task is to extract structured information from procurement documents (RFQs, vendor proposals, scorecards, etc.).

For each chunk of text provided, extract:
1. **Vendors**: Company names, locations, certifications, quality claims
2. **Requirements**: Buyer needs, specifications, measurable criteria (response time, availability, etc.)
3. **Offerings**: Vendor proposals, solutions, delivery timelines, support models
4. **Prices**: Unit costs, total costs, discounts, payment terms, volume pricing
5. **Findings**: Risks (delivery delays, vendor viability), gaps (missing info), opportunities (cost savings, value-adds), negotiation points

**Guidelines**:
- Extract ONLY what is explicitly stated in the text; do not infer or hallucinate.
- Always include evidence_snippet: the exact text supporting each extraction.
- For prices: extract numeric values only (no '$' or 'USD'), store separately in 'currency' field.
- For vendors: if a company is mentioned multiple times with different info (e.g., location, certifications), create separate extractions and let the linking phase merge them.
- Confidence score: 1.0 if text is explicit and clear, 0.7-0.9 if text is implicit or ambiguous, <0.7 if you had to infer significantly.
- If text is unclear or contradictory, note it in extraction_notes rather than guessing.

Return JSON following the ChunkExtractionResult schema.
"""


def build_extraction_prompt(chunk_text: str, chunk_id: str | None = None) -> str:
    """Build the user prompt for extraction of a single chunk."""
    prompt = f"""Extract structured procurement data from the following document chunk.

Chunk ID: {chunk_id or 'unknown'}

--- BEGIN CHUNK ---
{chunk_text}
--- END CHUNK ---

Return a JSON object matching the ChunkExtractionResult schema.
Be strict about only extracting what is explicitly stated.
Include evidence_snippet for every extracted entity.
"""
    return prompt

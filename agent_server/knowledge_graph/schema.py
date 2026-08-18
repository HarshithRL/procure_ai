"""Node/edge type definitions (Vendor, Article, Price, Term, Requirement, ...)
and the EvidenceRef structure (document, page/sheet, snippet) required on
every node and edge."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

__all__ = [
    "NodeType",
    "EdgeType",
    "NODE_TIER",
    "EDGE_TIER_1",
    "SPINE_PARENT",
    "NODE_DEPTH",
    "MAX_SPINE_DEPTH",
    "LEGACY_NODE_TYPES",
    "LEGACY_EDGE_TYPES",
    "canonical_node_type",
    "canonical_edge_type",
    "EvidenceRef",
    "Chunk",
    "Node",
    "Edge",
    "ExtractedNode",
    "ExtractedEdge",
    "ExtractionResult",
    "slugify",
]

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Normalize a name into a stable, lowercase, hyphenated slug used both as
    the node-id suffix and as the vault filename."""
    slug = _SLUG_RE.sub("-", value.strip().lower()).strip("-")
    return slug or "unnamed"


class EvidenceRef(BaseModel):
    """Reference to a specific location in a source document."""
    document_id: str
    locator: str  # e.g., "p.5", "table.2 row.3", "Sheet1!A5:D5"
    snippet: str = ""  # Optional text excerpt


def dedup_evidence(evidence: list[EvidenceRef]) -> list[EvidenceRef]:
    """Remove duplicate evidence references, keeping first occurrence."""
    seen = set()
    result = []
    for ref in evidence:
        key = (ref.document_id, ref.locator)
        if key not in seen:
            seen.add(key)
            result.append(ref)
    return result


class NodeType(str, Enum):
    """30 node types across 2 tiers: Tier-1 (8 anchor nodes, always visible,
    guaranteed connected via PROJECT) and Tier-2 (22 detail/derived nodes,
    hidden during overview mode to reduce clutter).
    
    See NODE_TIER dict below for tier assignment.
    """
    
    # === Tier-1: Anchor nodes (project-scoped procurement context) ===
    # The lineage spine reads:
    #   project -> requester -> sourcing_scope -> vendor -> offering -> offer_line
    # i.e. who asked, what they are buying, who bid, and what each bid contains.
    PROJECT = "project"                          # Root god-node
    REQUESTER = "requester"                      # Buyer-side owner of the need + budget
    SOURCING_SCOPE = "sourcing_scope"            # What is being procured (product/service/software)
    VENDOR = "vendor"                            # Supplier
    OFFERING = "offering"                        # One vendor's bid as a single comparable unit
    REQUIREMENT = "requirement"                  # Buyer need
    EVALUATION = "evaluation"                    # Score for vendor × requirement pair
    COMPARISON = "comparison"                    # Comparative analysis (vendors vs each other)
    RECOMMENDATION = "recommendation"            # Proposal to award contract to vendor X
    DECISION = "decision"                        # Final procurement decision (award or reject)
    CONTRACT = "contract"                        # Executed agreement after award
    
    # === Tier-2: Detail nodes (extracted from documents, hidden in overview) ===
    # Document provenance
    ARTICLE = "article"                          # Product/line item (extracted from XLSX, PDF, DOCX)
    PRICE_QUOTE = "price_quote"                  # Unit/box price for article + vendor

    # Offer decomposition (one BAFO cell each)
    OFFER_LINE = "offer_line"                    # One cost figure: component x year x amount
    ASSESSMENT = "assessment"                    # A score: scorecard/ecovadis/credit/architecture/security
    
    # Vendor-scoped detail
    ORGANIZATION = "organization"                # Vendor's legal entity + tax ID (was COMPANY_PROFILE)
    LOCATION = "location"                        # Vendor facility/HQ address
    CERTIFICATION = "certification"              # Third-party cert (ISO, CE, etc.)
    QUALITY_METRIC = "quality_metric"            # Quality score / defect rate / etc.
    SUPPORT_SERVICE = "support_service"          # Logistics, training, returns, etc.
    
    # Commercial & delivery
    COMMERCIAL_TERM = "commercial_term"          # Payment, MOQ, discount, lead time
    DELIVERY_TERM = "delivery_term"              # Shipping, incoterm, timeline (now separate from COMMERCIAL)
    WARRANTY = "warranty"                        # Warranty scope + duration
    
    # Requirement refinement
    SPECIFICATION = "specification"              # Technical detail (was implicit in REQUIREMENT)
    PERFORMANCE_METRIC = "performance_metric"    # Measurable requirement KPI
    
    # Intelligence layer
    FINDING = "finding"                          # Insight from doc analysis (gap, best practice, etc.)
    RISK = "risk"                                # Threat to procurement success
    OPPORTUNITY = "opportunity"                  # Upside or cost-saving lever
    INFORMATION_GAP = "information_gap"          # Missing data blocking evaluation
    NEGOTIATION_POINT = "negotiation_point"      # Lever (price, lead time, discount structure)
    
    # Business context
    STAKEHOLDER = "stakeholder"                  # Person with procurement decision/input power
    EVALUATION_COMMITTEE = "evaluation_committee" # Formal decision body
    BUSINESS_CONTEXT = "business_context"        # Strategic context (volume trends, supplier strategy)
    EXTERNAL_FACTOR = "external_factor"          # Market/regulatory/geo constraint (was implicit)
    
    # Deliverable
    DELIVERABLE = "deliverable"                  # Procurement output (Excel, dashboard, etc.)
    
    # Legacy alias (for compatibility during transition)
    SOURCE_DOCUMENT = "source_document"          # Uploaded vendor proposal doc
    MISSING_INFORMATION = "missing_information"  # Deprecated; use INFORMATION_GAP instead


class EdgeType(str, Enum):
    """21 edge types for procurement knowledge graphs. Categorized by tier:
    Tier-1 edges connect two Tier-1 nodes (visible in both detail + overview modes).
    Tier-2 edges involve at least one Tier-2 node (detail-mode only, hidden in overview).
    See NODE_TIER dict and code below for tier assignment.
    """
    
    # === Tier-1 edges: Project anchor → Anchor (always visible) ===
    HAS = "has"                               # project -> vendor | requirement | evaluation | recommendation | decision
    SELECTED_BY = "selected_by"               # vendor -> decision (award indication)
    INCLUDES = "includes"                     # recommendation -> decision (outcome of recommendation)

    # --- Lineage spine: who asked -> what for -> who bid -> what they offered ---
    HAS_REQUESTER = "has_requester"           # project -> requester
    REQUESTS = "requests"                     # requester -> sourcing_scope
    HAS_SCOPE = "has_scope"                   # project -> sourcing_scope (shortcut, keeps overview readable)
    HAS_REQUIREMENT = "has_requirement"       # sourcing_scope -> requirement
    INVITED = "invited"                       # sourcing_scope -> vendor
    SUBMITTED = "submitted"                   # vendor -> offering
    OFFERED_FOR = "offered_for"               # offering -> sourcing_scope (closes the loop)
    
    # === Tier-2 edges: Detail node relationships (detail-mode only) ===
    # Vendor-article relationships
    QUOTES = "quotes"                         # vendor -> price_quote
    PRICES_ARTICLE = "prices_article"         # price_quote -> article
    OFFERS_ARTICLE = "offers_article"         # vendor -> article (direct offer path)

    # Offer decomposition
    HAS_OFFER_LINE = "has_offer_line"         # offering -> offer_line
    HAS_ASSESSMENT = "has_assessment"         # offering | vendor -> assessment
    COVERS_REQUIREMENT = "covers_requirement" # offering -> requirement (attributes.status: met|partial|missing)
    INCLUDES_QUOTE = "includes_quote"         # offering -> price_quote (bridges BAFO envelope to the P*Q path)
    
    # Vendor detail composition
    HAS_ORGANIZATION = "has_organization"     # vendor -> organization
    HAS_LOCATION = "has_location"             # vendor -> location (facility or HQ)
    HAS_CERTIFICATION = "has_certification"   # vendor -> certification
    HAS_QUALITY_METRIC = "has_quality_metric" # vendor -> quality_metric
    HAS_SUPPORT = "has_support"               # vendor -> support_service
    HAS_COMMERCIAL = "has_commercial"         # vendor -> commercial_term (payment, MOQ, etc.)
    HAS_DELIVERY = "has_delivery"             # vendor -> delivery_term (incoterm, lead time)
    HAS_WARRANTY = "has_warranty"             # vendor -> warranty
    
    # Requirement detail composition
    HAS_SPECIFICATION = "has_specification"   # requirement -> specification
    HAS_METRIC = "has_metric"                 # requirement -> performance_metric
    
    # Matching/fulfillment
    MEETS = "meets"                           # vendor | article -> requirement (replaces MEETS_REQUIREMENT)
    ADDRESSES = "addresses"                   # organization | certification -> specification
    
    # Evaluation composition
    EVALUATED_AGAINST = "evaluated_against"   # evaluation -> requirement
    SCORED_VENDOR = "scored_vendor"           # evaluation -> vendor (replaces EVALUATED_FOR pattern)
    
    # Intelligence relationships
    DERIVED_FROM = "derived_from"             # finding | risk | opportunity -> source_document | article
    SUPPORTS_DECISION = "supports_decision"   # finding | risk | opportunity -> decision
    IDENTIFIED_GAP = "identified_gap"         # comparison -> information_gap
    
    # Recommendation composition
    GENERATED_FROM = "generated_from"         # recommendation -> evaluation
    CITES = "cites"                           # recommendation -> finding | risk | opportunity | negotiation_point
    
    # Governance / deliverables
    HAS_COMMITTEE = "has_committee"           # project -> evaluation_committee
    PRODUCES = "produces"                     # project -> deliverable

    # General metadata
    SUBMITTED_BY = "submitted_by"             # source_document -> vendor
    EXTRACTED_FROM = "extracted_from"         # any node -> source_document
    ASSIGNED_TO = "assigned_to"               # requirement | decision -> stakeholder
    RELATED_TO = "related_to"                 # general cross-links (fallback)


# === Tier assignment for overview/detail graph filtering ===
NODE_TIER = {
    # Tier-1 (11 anchor nodes: always visible, guaranteed connected via PROJECT).
    # The Tier-1 subgraph is exactly the lineage spine, so the UI overview mode
    # renders "who asked -> what for -> who bid -> what they offered".
    NodeType.PROJECT: 1,
    NodeType.REQUESTER: 1,
    NodeType.SOURCING_SCOPE: 1,
    NodeType.OFFERING: 1,
    NodeType.VENDOR: 1,
    NodeType.REQUIREMENT: 1,
    NodeType.EVALUATION: 1,
    NodeType.COMPARISON: 1,
    NodeType.RECOMMENDATION: 1,
    NodeType.DECISION: 1,
    NodeType.CONTRACT: 1,
    
    # Tier-2 (24 detail nodes: hidden in overview mode, full detail mode shows all)
    NodeType.ARTICLE: 2,
    NodeType.PRICE_QUOTE: 2,
    NodeType.OFFER_LINE: 2,
    NodeType.ASSESSMENT: 2,
    NodeType.ORGANIZATION: 2,
    NodeType.LOCATION: 2,
    NodeType.CERTIFICATION: 2,
    NodeType.QUALITY_METRIC: 2,
    NodeType.SUPPORT_SERVICE: 2,
    NodeType.COMMERCIAL_TERM: 2,
    NodeType.DELIVERY_TERM: 2,
    NodeType.WARRANTY: 2,
    NodeType.SPECIFICATION: 2,
    NodeType.PERFORMANCE_METRIC: 2,
    NodeType.FINDING: 2,
    NodeType.RISK: 2,
    NodeType.OPPORTUNITY: 2,
    NodeType.INFORMATION_GAP: 2,
    NodeType.NEGOTIATION_POINT: 2,
    NodeType.STAKEHOLDER: 2,
    NodeType.EVALUATION_COMMITTEE: 2,
    NodeType.BUSINESS_CONTEXT: 2,
    NodeType.EXTERNAL_FACTOR: 2,
    NodeType.DELIVERABLE: 2,
    # Deprecated aliases map to Tier-2
    NodeType.SOURCE_DOCUMENT: 2,
    NodeType.MISSING_INFORMATION: 2,
}

# === Tier assignment for edges ===
# Tier-1: both endpoints in Tier-1; Tier-2: at least one endpoint in Tier-2
EDGE_TIER_1 = {
    EdgeType.HAS,
    EdgeType.SELECTED_BY,
    EdgeType.INCLUDES,
    # Lineage spine — both endpoints are Tier-1 anchors
    EdgeType.HAS_REQUESTER,
    EdgeType.REQUESTS,
    EdgeType.HAS_SCOPE,
    EdgeType.HAS_REQUIREMENT,
    EdgeType.INVITED,
    EdgeType.SUBMITTED,
    EdgeType.OFFERED_FOR,
    EdgeType.COVERS_REQUIREMENT,
}


# === The lineage spine =====================================================
# `SPINE_PARENT` maps a node type to the (edge, parent type) that anchors it.
# This replaces the old "every node must reach PROJECT within 3 hops" rule,
# which was unenforceable once the spine grew past 3 levels — and which was
# never actually enforced, because the reachability check walked out-edges
# while the spine points away from PROJECT.
#
#   project(0) -> requester(1) -> sourcing_scope(2) -> vendor(3)
#              -> offering(4) -> offer_line(5) | assessment(5)
SPINE_PARENT: dict[NodeType, tuple[EdgeType, NodeType]] = {
    NodeType.REQUESTER: (EdgeType.HAS_REQUESTER, NodeType.PROJECT),
    NodeType.SOURCING_SCOPE: (EdgeType.REQUESTS, NodeType.REQUESTER),
    NodeType.VENDOR: (EdgeType.INVITED, NodeType.SOURCING_SCOPE),
    NodeType.OFFERING: (EdgeType.SUBMITTED, NodeType.VENDOR),
    NodeType.OFFER_LINE: (EdgeType.HAS_OFFER_LINE, NodeType.OFFERING),
    NodeType.ASSESSMENT: (EdgeType.HAS_ASSESSMENT, NodeType.OFFERING),
    NodeType.REQUIREMENT: (EdgeType.HAS_REQUIREMENT, NodeType.SOURCING_SCOPE),

    # Vendor-scoped detail
    NodeType.ARTICLE: (EdgeType.OFFERS_ARTICLE, NodeType.VENDOR),
    NodeType.PRICE_QUOTE: (EdgeType.QUOTES, NodeType.VENDOR),
    NodeType.ORGANIZATION: (EdgeType.HAS_ORGANIZATION, NodeType.VENDOR),
    NodeType.LOCATION: (EdgeType.HAS_LOCATION, NodeType.VENDOR),
    NodeType.CERTIFICATION: (EdgeType.HAS_CERTIFICATION, NodeType.VENDOR),
    NodeType.QUALITY_METRIC: (EdgeType.HAS_QUALITY_METRIC, NodeType.VENDOR),
    NodeType.SUPPORT_SERVICE: (EdgeType.HAS_SUPPORT, NodeType.VENDOR),
    NodeType.COMMERCIAL_TERM: (EdgeType.HAS_COMMERCIAL, NodeType.VENDOR),
    NodeType.DELIVERY_TERM: (EdgeType.HAS_DELIVERY, NodeType.VENDOR),
    NodeType.WARRANTY: (EdgeType.HAS_WARRANTY, NodeType.VENDOR),

    # Requirement-scoped detail
    NodeType.SPECIFICATION: (EdgeType.HAS_SPECIFICATION, NodeType.REQUIREMENT),
    NodeType.PERFORMANCE_METRIC: (EdgeType.HAS_METRIC, NodeType.REQUIREMENT),

    # Project-scoped context and outputs
    NodeType.EVALUATION: (EdgeType.HAS, NodeType.PROJECT),
    NodeType.COMPARISON: (EdgeType.HAS, NodeType.PROJECT),
    NodeType.RECOMMENDATION: (EdgeType.HAS, NodeType.PROJECT),
    NodeType.DECISION: (EdgeType.HAS, NodeType.PROJECT),
    NodeType.CONTRACT: (EdgeType.HAS, NodeType.PROJECT),
    NodeType.STAKEHOLDER: (EdgeType.HAS, NodeType.PROJECT),
    NodeType.EVALUATION_COMMITTEE: (EdgeType.HAS_COMMITTEE, NodeType.PROJECT),
    NodeType.BUSINESS_CONTEXT: (EdgeType.HAS, NodeType.PROJECT),
    NodeType.EXTERNAL_FACTOR: (EdgeType.HAS, NodeType.PROJECT),
    NodeType.DELIVERABLE: (EdgeType.PRODUCES, NodeType.PROJECT),
    NodeType.SOURCE_DOCUMENT: (EdgeType.HAS, NodeType.PROJECT),
}


def _compute_node_depth() -> dict[NodeType, int]:
    """Distance from PROJECT along `SPINE_PARENT`, derived not hand-maintained."""
    depths: dict[NodeType, int] = {NodeType.PROJECT: 0}

    def resolve(node_type: NodeType, seen: frozenset[NodeType]) -> int:
        if node_type in depths:
            return depths[node_type]
        parent = SPINE_PARENT.get(node_type)
        if parent is None or node_type in seen:
            return 1  # unanchored types hang directly off PROJECT
        depths[node_type] = resolve(parent[1], seen | {node_type}) + 1
        return depths[node_type]

    for node_type in NodeType:
        resolve(node_type, frozenset())
    return depths


NODE_DEPTH: dict[NodeType, int] = _compute_node_depth()
MAX_SPINE_DEPTH = max(NODE_DEPTH.values())


# === Legacy aliases ========================================================
# Deprecated members are never removed (stored rows would stop parsing) and
# never rewritten in place. `canonical_*` is applied on READ paths only.
LEGACY_NODE_TYPES: frozenset[NodeType] = frozenset(
    {NodeType.MISSING_INFORMATION, NodeType.SOURCE_DOCUMENT}
)
LEGACY_EDGE_TYPES: frozenset[EdgeType] = frozenset({EdgeType.MEETS})

_CANONICAL_NODE_TYPE: dict[NodeType, NodeType] = {
    NodeType.MISSING_INFORMATION: NodeType.INFORMATION_GAP,
}
_CANONICAL_EDGE_TYPE: dict[EdgeType, EdgeType] = {
    EdgeType.MEETS: EdgeType.COVERS_REQUIREMENT,
}


def canonical_node_type(node_type: NodeType) -> NodeType:
    """Map a deprecated node type onto its replacement (read paths only)."""
    return _CANONICAL_NODE_TYPE.get(node_type, node_type)


def canonical_edge_type(edge_type: EdgeType) -> EdgeType:
    """Map a deprecated edge type onto its replacement (read paths only)."""
    return _CANONICAL_EDGE_TYPE.get(edge_type, edge_type)


class Chunk(BaseModel):
    """A parsed unit of a source document with a precise evidence locator."""

    document_id: str
    locator: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Node(BaseModel):
    """A knowledge-graph entity. `id` follows the `{type}--{slug}` convention
    used to derive the vault note path (see `agent_server.knowledge_graph.vault`)."""

    id: str
    type: NodeType
    name: str
    project_id: int
    attributes: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceRef] = Field(default_factory=list)

    @field_validator("evidence")
    @classmethod
    def _require_evidence(cls, value: list[EvidenceRef]) -> list[EvidenceRef]:
        if not value:
            raise ValueError("Node must carry at least one EvidenceRef")
        return value

    @staticmethod
    def make_id(node_type: NodeType, slug: str) -> str:
        return f"{node_type.value}--{slug}"


class Edge(BaseModel):
    """A directed, typed relationship between two nodes, each identified by
    their global `Node.id`."""

    id: str = ""
    type: EdgeType
    source: str
    target: str
    project_id: int
    attributes: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceRef] = Field(default_factory=list)

    @field_validator("evidence")
    @classmethod
    def _require_evidence(cls, value: list[EvidenceRef]) -> list[EvidenceRef]:
        if not value:
            raise ValueError("Edge must carry at least one EvidenceRef")
        return value

    @model_validator(mode="after")
    def _default_id(self) -> Edge:
        if not self.id:
            self.id = f"{self.source}=={self.type.value}=>{self.target}"
        return self


class ExtractedNode(BaseModel):
    """LLM-facing node payload for a single chunk, before the link node
    assigns a global id and resolves it against the rest of the project."""

    type: NodeType
    slug: str = Field(description="Short, stable, url-safe local slug, e.g. 'hisener' or '4045528'.")
    name: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceRef]

    @field_validator("type", mode="before")
    @classmethod
    def normalize_node_type(cls, v: Any) -> NodeType:
        """Normalize node type string from LLM output (handles UPPERCASE, PascalCase, snake_case)."""
        if isinstance(v, NodeType):
            return v
        if isinstance(v, str):
            # Normalize: convert PascalCase/UPPERCASE to snake_case
            # e.g. "NEGOTIATION_POINT" → "negotiation_point"
            #      "NegotiationPoint" → "negotiation_point"
            #      "negotiation_point" → "negotiation_point"
            
            # First convert PascalCase to snake_case using regex
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', v)  # PascalCase → snake_case
            normalized = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
            
            # Try normalized version
            try:
                return NodeType(normalized)
            except ValueError:
                pass
            
            # Fallback: raise with helpful message
            raise ValueError(f"'{v}' is not a valid NodeType. Valid values: {[m.value for m in NodeType]}")
        raise ValueError(f"NodeType must be a string, got {type(v)}")


class ExtractedEdge(BaseModel):
    """LLM-facing edge payload referencing `ExtractedNode.slug` values rather
    than global node ids (which the link node has not assigned yet)."""

    type: EdgeType
    source_slug: str
    target_slug: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceRef]

    @field_validator("type", mode="before")
    @classmethod
    def normalize_edge_type(cls, v: Any) -> EdgeType:
        """Normalize edge type string from LLM output (handles UPPERCASE, PascalCase, snake_case)."""
        if isinstance(v, EdgeType):
            return v
        if isinstance(v, str):
            # Normalize: convert PascalCase/UPPERCASE to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', v)
            normalized = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
            
            # Try normalized version
            try:
                return EdgeType(normalized)
            except ValueError:
                pass
            
            # Fallback: raise with helpful message
            raise ValueError(f"'{v}' is not a valid EdgeType. Valid values: {[m.value for m in EdgeType]}")
        raise ValueError(f"EdgeType must be a string, got {type(v)}")


class ExtractionResult(BaseModel):
    """Structured-output contract for the LLM extraction step, produced once
    per document chunk."""

    nodes: list[ExtractedNode] = Field(default_factory=list)
    edges: list[ExtractedEdge] = Field(default_factory=list)

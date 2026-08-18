"""Extract node: LLM entity/edge extraction using Claude structured output."""

from __future__ import annotations

import json
import logging
from typing import Optional

from agent_server.ingestion.extraction_schema import (
    ChunkExtractionResult,
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_prompt,
)
from agent_server.ingestion.state import IngestionState
from agent_server.knowledge_graph.schema import (
    EvidenceRef,
    ExtractedEdge,
    ExtractedNode,
    NodeType,
    EdgeType,
    slugify,
)
from shared_library.model_factory import resolve_chat_model

logger = logging.getLogger(__name__)


def extract_node(state: IngestionState) -> dict:
    """Extract entities and edges from chunk using Claude structured output.
    
    For each chunk, invoke Claude with structured output to extract:
    - Vendors (organization nodes)
    - Requirements (requirement nodes)
    - Offerings & prices (offering + offer_line nodes)
    - Findings (risk, opportunity, gap nodes)
    
    Returns:
    - entities: list[ExtractedNode] — vendor, requirement, offering, finding nodes
    - edges: list[ExtractedEdge] — project->vendor, vendor->offering, etc.
    - deferred_edges: list[ExtractedEdge] — edges with missing endpoints (resolved in link phase)
    """
    chunk = state.get("chunk")
    if not chunk:
        return {
            "entities": [],
            "edges": [],
            "deferred_edges": [],
        }
    
    chunk_text = chunk.text
    chunk_id = chunk.document_id
    project_id = state.get("project_id")
    
    # Resolve the LLM (default: balanced profile)
    try:
        llm = resolve_chat_model("balanced")
    except Exception as e:
        logger.error("Failed to resolve LLM: %s", e)
        return {
            "entities": [],
            "edges": [],
            "deferred_edges": [],
            "errors": [f"LLM resolution failed: {str(e)}"],
        }
    
    # Use LangChain structured output to extract
    structured_llm = llm.with_structured_output(ChunkExtractionResult)
    
    # Build prompt and invoke
    user_prompt = build_extraction_prompt(chunk_text, chunk_id)
    
    try:
        result: ChunkExtractionResult = structured_llm.invoke([
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ])
    except Exception as e:
        logger.error("LLM extraction failed for chunk %s: %s", chunk_id, e)
        return {
            "entities": [],
            "edges": [],
            "deferred_edges": [],
            "errors": [f"Extraction failed: {str(e)}"],
        }
    
    # Convert extraction result to nodes and edges
    entities: list[ExtractedNode] = []
    edges: list[ExtractedEdge] = []
    deferred_edges: list[ExtractedEdge] = []
    evidence_rejected = 0
    
    evidence_ref = EvidenceRef(
        document_id=chunk_id,
        locator=chunk.metadata.get("locator", "unknown"),
        snippet=chunk_text[:200],
    )
    
    # Extract vendor nodes
    for vendor in result.vendors:
        node = ExtractedNode(
            node_type=NodeType.VENDOR,
            label=vendor.name,
            slug=slugify(vendor.name),
            description=f"Domain: {vendor.domain}" if vendor.domain else None,
            evidence=[evidence_ref],
            metadata={
                "domain": vendor.domain,
                "location": vendor.location,
                "certifications": vendor.certifications,
                "quality_summary": vendor.quality_summary,
            },
            confidence=result.confidence_score,
        )
        entities.append(node)
        
        # Edge: project -> vendor (deferred until link phase has project node)
        deferred_edges.append(ExtractedEdge(
            source_type=NodeType.PROJECT,
            source_slug="project",  # Will be resolved in link phase
            target_type=NodeType.VENDOR,
            target_slug=node.slug,
            edge_type=EdgeType.HAS,
            evidence=[evidence_ref],
            confidence=result.confidence_score,
        ))
    
    # Extract requirement nodes
    for req in result.requirements:
        node = ExtractedNode(
            node_type=NodeType.REQUIREMENT,
            label=req.title,
            slug=slugify(req.title),
            description=req.description,
            evidence=[evidence_ref],
            metadata={
                "category": req.category,
                "measurable": req.measurable,
                "metric": req.metric,
            },
            confidence=result.confidence_score,
        )
        entities.append(node)
        
        # Edge: project -> requirement
        deferred_edges.append(ExtractedEdge(
            source_type=NodeType.PROJECT,
            source_slug="project",
            target_type=NodeType.REQUIREMENT,
            target_slug=node.slug,
            edge_type=EdgeType.HAS_REQUIREMENT,
            evidence=[evidence_ref],
            confidence=result.confidence_score,
        ))
    
    # Extract offering nodes (from offerings list)
    for offering in result.offerings:
        offering_slug = slugify(f"{offering.vendor_name}-{offering.offering_title or 'offering'}")
        node = ExtractedNode(
            node_type=NodeType.OFFERING,
            label=offering.offering_title or f"{offering.vendor_name} Offering",
            slug=offering_slug,
            description=offering.overview,
            evidence=[evidence_ref],
            metadata={
                "vendor_name": offering.vendor_name,
                "delivery_timeline": offering.delivery_timeline,
                "support_model": offering.support_model,
            },
            confidence=result.confidence_score,
        )
        entities.append(node)
        
        # Edge: vendor -> offering (deferred, vendor may not yet be linked)
        deferred_edges.append(ExtractedEdge(
            source_type=NodeType.VENDOR,
            source_slug=slugify(offering.vendor_name),
            target_type=NodeType.OFFERING,
            target_slug=offering_slug,
            edge_type=EdgeType.HAS_OFFERING,
            evidence=[evidence_ref],
            confidence=result.confidence_score,
        ))
    
    # Extract price/offer_line nodes from prices
    for price in result.prices:
        # Create or link to offering
        offering_slug = slugify(f"{price.offering_vendor}-{price.article_or_component or 'offering'}")
        
        offer_line_slug = slugify(f"{offering_slug}-{price.article_or_component or 'line'}")
        node = ExtractedNode(
            node_type=NodeType.OFFER_LINE,
            label=f"{price.offering_vendor} - {price.article_or_component or 'Line Item'}",
            slug=offer_line_slug,
            description=f"Unit: {price.unit_price} {price.currency}" if price.unit_price else None,
            evidence=[evidence_ref],
            metadata={
                "vendor_name": price.offering_vendor,
                "article": price.article_or_component,
                "quantity": price.quantity,
                "unit_price": price.unit_price,
                "currency": price.currency,
                "total_cost": price.total_cost,
                "payment_terms": price.payment_terms,
                "discount_info": price.discount_info,
            },
            confidence=result.confidence_score,
        )
        entities.append(node)
        
        # Edge: offering -> offer_line
        deferred_edges.append(ExtractedEdge(
            source_type=NodeType.OFFERING,
            source_slug=offering_slug,
            target_type=NodeType.OFFER_LINE,
            target_slug=offer_line_slug,
            edge_type=EdgeType.INCLUDES,
            evidence=[evidence_ref],
            confidence=result.confidence_score,
        ))
    
    # Extract finding nodes (risks, gaps, opportunities)
    for finding in result.findings:
        finding_type_map = {
            "risk": NodeType.RISK,
            "gap": NodeType.INFORMATION_GAP,
            "opportunity": NodeType.OPPORTUNITY,
            "negotiation_point": NodeType.NEGOTIATION_POINT,
            "best_practice": NodeType.FINDING,
            "concern": NodeType.RISK,
        }
        node_type = finding_type_map.get(finding.finding_type, NodeType.FINDING)
        
        node = ExtractedNode(
            node_type=node_type,
            label=finding.title,
            slug=slugify(finding.title),
            description=finding.description,
            evidence=[evidence_ref],
            metadata={
                "finding_type": finding.finding_type,
                "severity": finding.severity,
                "related_vendors": finding.related_vendors,
                "related_requirements": finding.related_requirements,
            },
            confidence=result.confidence_score,
        )
        entities.append(node)
        
        # Edge: project -> finding
        deferred_edges.append(ExtractedEdge(
            source_type=NodeType.PROJECT,
            source_slug="project",
            target_type=node_type,
            target_slug=node.slug,
            edge_type=EdgeType.HAS,
            evidence=[evidence_ref],
            confidence=result.confidence_score,
        ))
    
    return {
        "entities": entities,
        "edges": [],  # No fully-resolved edges in this chunk (all vendor/project relationships are deferred)
        "deferred_edges": deferred_edges,
        "evidence_rejected": evidence_rejected,
    }

"""Orchestrate discipline-specific evaluation checks."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_checks_for_discipline(
    discipline: str, 
    strategy: dict[str, Any], 
    doctrines: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Run evaluation checks for a specific discipline.
    
    Args:
        discipline: The discipline to evaluate (e.g., 'psychology', 'design')
        strategy: The strategy content to evaluate
        doctrines: Loaded doctrine configurations
        
    Returns:
        Tuple of (findings, scores, recommendations)
    """
    logger.info(f"Running checks for discipline: {discipline}")
    
    # Get doctrine for this discipline
    doctrine = doctrines.get(discipline, {})
    if not doctrine:
        logger.warning(f"No doctrine found for discipline: {discipline}")
        return [], {"overall": 0.0}, [f"No evaluation criteria available for {discipline}"]
    
    findings = []
    scores = {"overall": 0.0}
    recommendations = []
    
    # Extract strategy content for analysis
    content = strategy.get("content", "")
    title = strategy.get("title", "")
    summary = strategy.get("summary", "")
    
    # Combine all text for analysis
    full_text = f"{title} {summary} {content}".strip()
    
    if discipline == "psychology":
        findings, scores, recommendations = _check_psychology(full_text, doctrine)
    elif discipline == "design":
        findings, scores, recommendations = _check_design(strategy, doctrine)
    elif discipline == "communication":
        findings, scores, recommendations = _check_communication(full_text, doctrine)
    elif discipline == "accessibility":
        findings, scores, recommendations = _check_accessibility(strategy, doctrine)
    elif discipline == "brand_science":
        findings, scores, recommendations = _check_brand_science(full_text, doctrine)
    elif discipline == "economics":
        findings, scores, recommendations = _check_economics(full_text, doctrine)
    elif discipline == "legal":
        findings, scores, recommendations = _check_legal(full_text, doctrine)
    else:
        # Generic check for unknown disciplines
        findings, scores, recommendations = _check_generic(discipline, full_text, doctrine)
    
    logger.debug(f"Discipline {discipline} evaluation complete: {len(findings)} findings, score: {scores.get('overall', 0)}")
    return findings, scores, recommendations


def _check_psychology(text: str, doctrine: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Check psychology-related aspects."""
    findings = []
    scores = {"overall": 0.8}  # Start with good score
    recommendations = []
    
    # Check for psychological reactance phrases
    reactance_phrases = doctrine.get("reactance_phrases", [])
    if isinstance(reactance_phrases, str):
        reactance_phrases = [reactance_phrases]
    
    reactance_found = []
    for phrase in reactance_phrases:
        if phrase.lower() in text.lower():
            reactance_found.append(phrase)
    
    if reactance_found:
        finding = {
            "id": "psych_reactance",
            "severity": "warning",
            "title": "Psychological reactance detected",
            "description": f"Found potentially triggering phrases: {', '.join(reactance_found)}"
        }
        findings.append(finding)
        scores["overall"] -= 0.3
        recommendations.append("Consider rewording to reduce psychological reactance")
    
    # Check COM-B model elements if configured
    comb_elements = doctrine.get("comb_elements", {})
    if comb_elements:
        capability_keywords = comb_elements.get("capability", [])
        motivation_keywords = comb_elements.get("motivation", [])
        opportunity_keywords = comb_elements.get("opportunity", [])
        
        found_elements = []
        if any(kw.lower() in text.lower() for kw in capability_keywords):
            found_elements.append("capability")
        if any(kw.lower() in text.lower() for kw in motivation_keywords):
            found_elements.append("motivation")
        if any(kw.lower() in text.lower() for kw in opportunity_keywords):
            found_elements.append("opportunity")
        
        if len(found_elements) < 2:
            finding = {
                "id": "psych_comb_incomplete",
                "severity": "info",
                "title": "Incomplete COM-B coverage",
                "description": f"Only {len(found_elements)} of 3 COM-B elements present: {', '.join(found_elements)}"
            }
            findings.append(finding)
            recommendations.append("Consider addressing all COM-B elements (Capability, Opportunity, Motivation)")
    
    return findings, scores, recommendations


def _check_design(strategy: dict[str, Any], doctrine: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Check design-related aspects using NN/g heuristics."""
    findings = []
    scores = {"overall": 0.7}
    recommendations = []
    
    # Check for visual elements or design proof
    has_visuals = any(key in strategy for key in ["images", "mockups", "wireframes", "prototypes"])
    
    if not has_visuals:
        finding = {
            "id": "design_no_proof",
            "severity": "warning", 
            "title": "No design proof provided",
            "description": "Strategy lacks visual elements or design artifacts"
        }
        findings.append(finding)
        scores["overall"] -= 0.4
        recommendations.append("Provide mockups, wireframes, or visual examples to support the strategy")
    
    # Check usability heuristics if configured
    heuristics = doctrine.get("heuristics", {})
    if heuristics:
        for heuristic_id, heuristic_info in heuristics.items():
            # Simple check for heuristic keywords in strategy
            keywords = heuristic_info.get("keywords", [])
            if keywords and not any(kw.lower() in str(strategy).lower() for kw in keywords):
                finding = {
                    "id": f"design_heuristic_{heuristic_id}",
                    "severity": "info",
                    "title": f"Missing heuristic: {heuristic_info.get('title', heuristic_id)}",
                    "description": f"Consider {heuristic_info.get('description', 'this usability principle')}"
                }
                findings.append(finding)
    
    return findings, scores, recommendations


def _check_communication(text: str, doctrine: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Check communication effectiveness."""
    findings = []
    scores = {"overall": 0.8}
    recommendations = []
    
    # Check message map structure
    message_map = doctrine.get("message_map", {})
    if message_map:
        required_elements = message_map.get("required_elements", [])
        missing_elements = []
        
        for element in required_elements:
            element_keywords = message_map.get(f"{element}_keywords", [])
            if not any(kw.lower() in text.lower() for kw in element_keywords):
                missing_elements.append(element)
        
        if missing_elements:
            finding = {
                "id": "comm_message_map_incomplete",
                "severity": "info",
                "title": "Incomplete message structure",
                "description": f"Missing message elements: {', '.join(missing_elements)}"
            }
            findings.append(finding)
            recommendations.append("Ensure all key message elements are present and clear")
    
    return findings, scores, recommendations


def _check_accessibility(strategy: dict[str, Any], doctrine: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Check accessibility compliance."""
    findings = []
    scores = {"overall": 0.9}
    recommendations = []
    
    # Check WCAG guidelines if configured
    wcag_guidelines = doctrine.get("wcag_guidelines", {})
    if wcag_guidelines:
        # Check for alt text mention
        if "alt" not in str(strategy).lower() and "alternative" not in str(strategy).lower():
            finding = {
                "id": "a11y_alt_text",
                "severity": "warning",
                "title": "No alternative text consideration",
                "description": "Strategy should address alternative text for images"
            }
            findings.append(finding)
            scores["overall"] -= 0.2
            recommendations.append("Include alternative text planning for visual content")
    
    return findings, scores, recommendations


def _check_brand_science(text: str, doctrine: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Check brand science aspects."""
    findings = []
    scores = {"overall": 0.7}
    recommendations = []
    
    # Check for brand positioning elements
    brand_elements = doctrine.get("brand_elements", [
        "positioning", "differentiation", "value proposition", "brand promise",
        "brand personality", "target audience", "competitive advantage"
    ])
    
    missing_elements = []
    for element in brand_elements:
        if element.lower() not in text.lower():
            missing_elements.append(element)
    
    if missing_elements:
        # Penalize score based on missing elements
        penalty = min(0.5, len(missing_elements) * 0.1)
        scores["overall"] -= penalty
        
        finding = {
            "id": "brand_missing_elements",
            "severity": "warning" if len(missing_elements) > 3 else "info",
            "title": "Missing brand science elements",
            "description": f"Strategy lacks key brand elements: {', '.join(missing_elements[:3])}{'...' if len(missing_elements) > 3 else ''}"
        }
        findings.append(finding)
        recommendations.append("Include core brand positioning and differentiation elements")
    
    # Check for brand consistency indicators
    consistency_keywords = doctrine.get("consistency_keywords", [
        "consistent", "unified", "cohesive", "aligned", "integrated"
    ])
    
    if not any(kw.lower() in text.lower() for kw in consistency_keywords):
        finding = {
            "id": "brand_consistency_missing",
            "severity": "info",
            "title": "No brand consistency consideration",
            "description": "Strategy doesn't address brand consistency across touchpoints"
        }
        findings.append(finding)
        recommendations.append("Address brand consistency across all customer touchpoints")
    
    return findings, scores, recommendations


def _check_economics(text: str, doctrine: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Check economic viability and business model aspects."""
    findings = []
    scores = {"overall": 0.8}
    recommendations = []
    
    # Check for key economic concepts
    economic_concepts = doctrine.get("economic_concepts", [
        "roi", "return on investment", "cost", "revenue", "profit", "budget",
        "pricing", "value", "market size", "competition", "demand", "supply"
    ])
    
    missing_concepts = []
    for concept in economic_concepts:
        if concept.lower() not in text.lower():
            missing_concepts.append(concept)
    
    if len(missing_concepts) > len(economic_concepts) * 0.7:  # If more than 70% missing
        scores["overall"] -= 0.3
        finding = {
            "id": "econ_insufficient_analysis",
            "severity": "warning",
            "title": "Insufficient economic analysis",
            "description": "Strategy lacks key economic considerations like ROI, costs, or market dynamics"
        }
        findings.append(finding)
        recommendations.append("Include economic feasibility analysis with costs, ROI, and market considerations")
    
    # Check for business model elements
    business_model_elements = doctrine.get("business_model_elements", [
        "revenue model", "value proposition", "cost structure", "target market",
        "channels", "customer segments", "competitive advantage"
    ])
    
    model_elements_present = sum(1 for element in business_model_elements if element.lower() in text.lower())
    if model_elements_present < len(business_model_elements) * 0.4:  # Less than 40% present
        scores["overall"] -= 0.2
        finding = {
            "id": "econ_weak_business_model",
            "severity": "info",
            "title": "Weak business model definition",
            "description": "Strategy should better define the underlying business model"
        }
        findings.append(finding)
        recommendations.append("Strengthen business model definition with clear value proposition and revenue streams")
    
    return findings, scores, recommendations


def _check_legal(text: str, doctrine: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Check legal compliance and risk factors."""
    findings = []
    scores = {"overall": 0.9}  # Start high, deduct for issues
    recommendations = []
    
    # Check for compliance considerations
    compliance_keywords = doctrine.get("compliance_keywords", [
        "gdpr", "privacy", "data protection", "terms", "conditions", "disclaimer",
        "compliance", "regulatory", "legal", "copyright", "trademark"
    ])
    
    compliance_mentions = sum(1 for kw in compliance_keywords if kw.lower() in text.lower())
    if compliance_mentions == 0:
        scores["overall"] -= 0.3
        finding = {
            "id": "legal_no_compliance",
            "severity": "warning",
            "title": "No legal compliance consideration",
            "description": "Strategy doesn't address legal compliance, privacy, or regulatory requirements"
        }
        findings.append(finding)
        recommendations.append("Consider legal compliance requirements including privacy, data protection, and industry regulations")
    
    # Check for risky language patterns
    risky_phrases = doctrine.get("risky_phrases", [
        "guaranteed", "risk-free", "100% effective", "never fails", "always works",
        "miracle", "instant", "overnight success", "no effort required"
    ])
    
    risks_found = []
    for phrase in risky_phrases:
        if phrase.lower() in text.lower():
            risks_found.append(phrase)
    
    if risks_found:
        scores["overall"] -= min(0.4, len(risks_found) * 0.1)
        finding = {
            "id": "legal_risky_claims",
            "severity": "error",
            "title": "Potentially problematic claims",
            "description": f"Strategy contains risky language that may lead to legal issues: {', '.join(risks_found[:3])}"
        }
        findings.append(finding)
        recommendations.append("Remove or qualify absolute claims to avoid potential legal liability")
    
    # Check for intellectual property considerations
    ip_keywords = doctrine.get("ip_keywords", [
        "copyright", "trademark", "patent", "intellectual property", "licensing",
        "fair use", "attribution", "original content"
    ])
    
    if not any(kw.lower() in text.lower() for kw in ip_keywords):
        finding = {
            "id": "legal_no_ip_consideration",
            "severity": "info",
            "title": "No intellectual property consideration",
            "description": "Strategy doesn't address intellectual property rights or licensing"
        }
        findings.append(finding)
        recommendations.append("Consider intellectual property rights for content, imagery, and branding elements")
    
    return findings, scores, recommendations


def _check_generic(discipline: str, text: str, doctrine: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, float], list[str]]:
    """Generic check for unknown disciplines."""
    findings = []
    scores = {"overall": 0.5}  # Neutral score for unknown disciplines
    recommendations = []
    
    finding = {
        "id": f"{discipline}_unknown",
        "severity": "info", 
        "title": f"Unknown discipline: {discipline}",
        "description": f"No specific evaluation criteria available for {discipline}"
    }
    findings.append(finding)
    recommendations.append(f"Define specific evaluation criteria for {discipline}")
    
    return findings, scores, recommendations


__all__ = ["run_checks_for_discipline"]
"""Strategy synthesis and brief generation from processed documents and frameworks."""

from __future__ import annotations

import logging
from datetime import datetime

from jinja2 import Template
from pydantic import BaseModel, Field

from .document_processor import ProcessedDocument
from .pie_scorer import InitiativePortfolio, StrategicInitiative
from .strategyzer_mapper import (
    BusinessModelCanvas,
    StrategyzerMapper,
    ValuePropositionCanvas,
)

logger = logging.getLogger(__name__)


class StrategyBrief(BaseModel):
    """Complete strategy brief with executive summary, analysis, and recommendations."""

    # Metadata
    title: str
    created_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    authors: list[str] = Field(default_factory=list)

    # Executive Summary
    executive_summary: str = ""
    key_findings: list[str] = Field(default_factory=list)
    strategic_recommendations: list[str] = Field(default_factory=list)

    # Analysis Sections
    situation_analysis: str = ""
    market_analysis: str = ""
    competitive_landscape: str = ""
    internal_capabilities: str = ""

    # Strategic Framework
    business_model_canvas: BusinessModelCanvas | None = None
    value_proposition_canvas: ValuePropositionCanvas | None = None

    # Implementation
    strategic_initiatives: list[StrategicInitiative] = Field(default_factory=list)
    implementation_roadmap: str = ""
    success_metrics: list[str] = Field(default_factory=list)

    # Supporting Information
    evidence_sources: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    risks_mitigation: dict[str, str] = Field(default_factory=dict)

    # Quality Metrics
    evidence_strength: str = ""
    confidence_level: str = ""
    completeness_score: float = 0.0


class StrategySynthesizer:
    """Synthesizes strategy briefs from processed documents and analysis."""

    def __init__(self):
        self.mapper = StrategyzerMapper()
        self.brief_template = self._load_brief_template()

    def synthesize_strategy(
        self,
        documents: list[ProcessedDocument],
        portfolio: InitiativePortfolio | None = None,
        brief_title: str = "Strategic Analysis Brief",
        authors: list[str] | None = None
    ) -> StrategyBrief:
        """Synthesize complete strategy brief from input documents."""

        logger.info(f"Synthesizing strategy brief from {len(documents)} documents")

        # Create base brief
        brief = StrategyBrief(
            title=brief_title,
            authors=authors or [],
            evidence_sources=[doc.filename for doc in documents]
        )

        # Generate strategic frameworks
        bmc = self.mapper.map_to_bmc(documents)
        vpc = self.mapper.map_to_vpc(documents)
        brief.business_model_canvas = bmc
        brief.value_proposition_canvas = vpc

        # Analyze documents for content sections
        brief.situation_analysis = self._generate_situation_analysis(documents)
        brief.market_analysis = self._generate_market_analysis(documents)
        brief.competitive_landscape = self._generate_competitive_analysis(documents)
        brief.internal_capabilities = self._generate_capabilities_analysis(documents)

        # Generate key findings and recommendations
        brief.key_findings = self._extract_key_findings(documents, bmc, vpc)
        brief.strategic_recommendations = self._generate_strategic_recommendations(documents, bmc, vpc)

        # Add strategic initiatives if provided
        if portfolio:
            brief.strategic_initiatives = portfolio.get_ranked_initiatives()
            brief.implementation_roadmap = self._generate_implementation_roadmap(portfolio)

        # Generate executive summary
        brief.executive_summary = self._generate_executive_summary(brief)

        # Calculate quality metrics
        brief.evidence_strength = self._assess_evidence_strength(documents, bmc, vpc)
        brief.confidence_level = self._assess_confidence_level(documents, bmc, vpc)
        brief.completeness_score = self._calculate_completeness_score(brief)

        # Generate success metrics and risk analysis
        brief.success_metrics = self._generate_success_metrics(bmc, vpc)
        brief.risks_mitigation = self._generate_risk_mitigation(documents, brief)
        brief.assumptions = self._extract_assumptions(documents, brief)

        logger.info(f"Strategy brief synthesized with {brief.completeness_score:.2f} completeness score")
        return brief

    def _generate_situation_analysis(self, documents: list[ProcessedDocument]) -> str:
        """Generate situation analysis from documents."""

        # Extract current state information
        situation_elements = []

        for doc in documents:
            # Look for situation-related content
            for section in doc.sections:
                content_lower = section.content.lower()
                if any(keyword in content_lower for keyword in [
                    'current', 'situation', 'status', 'position', 'state', 'challenge', 'problem'
                ]):
                    situation_elements.append(section.content[:200] + "...")

        if situation_elements:
            return "\n\n".join(situation_elements[:3])  # Top 3 most relevant
        else:
            return "Current situation analysis requires additional information from source documents."

    def _generate_market_analysis(self, documents: list[ProcessedDocument]) -> str:
        """Generate market analysis from documents."""

        market_elements = []

        for doc in documents:
            for section in doc.sections:
                content_lower = section.content.lower()
                if any(keyword in content_lower for keyword in [
                    'market', 'industry', 'segment', 'customer', 'demand', 'growth', 'size', 'trend'
                ]):
                    market_elements.append(section.content[:200] + "...")

        if market_elements:
            return "\n\n".join(market_elements[:3])
        else:
            return "Market analysis requires additional market research and industry data."

    def _generate_competitive_analysis(self, documents: list[ProcessedDocument]) -> str:
        """Generate competitive landscape analysis."""

        competitive_elements = []

        for doc in documents:
            for section in doc.sections:
                content_lower = section.content.lower()
                if any(keyword in content_lower for keyword in [
                    'competitor', 'competition', 'rival', 'alternative', 'benchmark', 'versus', 'compare'
                ]):
                    competitive_elements.append(section.content[:200] + "...")

        if competitive_elements:
            return "\n\n".join(competitive_elements[:3])
        else:
            return "Competitive analysis requires additional competitor intelligence and market positioning data."

    def _generate_capabilities_analysis(self, documents: list[ProcessedDocument]) -> str:
        """Generate internal capabilities analysis."""

        capabilities_elements = []

        for doc in documents:
            for section in doc.sections:
                content_lower = section.content.lower()
                if any(keyword in content_lower for keyword in [
                    'capability', 'strength', 'weakness', 'resource', 'skill', 'competency', 'asset', 'infrastructure'
                ]):
                    capabilities_elements.append(section.content[:200] + "...")

        if capabilities_elements:
            return "\n\n".join(capabilities_elements[:3])
        else:
            return "Internal capabilities analysis requires additional organizational and resource assessment data."

    def _extract_key_findings(
        self,
        documents: list[ProcessedDocument],
        bmc: BusinessModelCanvas,
        vpc: ValuePropositionCanvas
    ) -> list[str]:
        """Extract key strategic findings."""

        findings = []

        # Document-based findings
        total_entities = sum(len(doc.entities) for doc in documents)
        if total_entities > 20:
            findings.append(f"Rich data set with {total_entities} identified entities across {len(documents)} documents")

        # BMC findings
        if len(bmc.value_propositions) > 0:
            findings.append(f"Identified {len(bmc.value_propositions)} distinct value propositions")

        if len(bmc.customer_segments) > 3:
            findings.append("Multi-segment strategy requiring differentiated approaches")
        elif len(bmc.customer_segments) == 1:
            findings.append("Focused single-segment strategy with clear target market")

        # VPC findings
        fit_assessment = vpc.fit_assessment.get("overall_fit", "")
        if "Strong" in fit_assessment:
            findings.append("Strong product-market fit indicated by aligned customer needs and value delivery")
        elif "Weak" in fit_assessment:
            findings.append("Weak product-market fit requiring value proposition refinement")

        # Evidence-based findings
        strong_evidence_sections = []
        for section, sources in bmc.evidence_sources.items():
            if len(sources) >= 2:
                strong_evidence_sections.append(section)

        if strong_evidence_sections:
            findings.append(f"Strong evidence support for: {', '.join(strong_evidence_sections)}")

        return findings[:5]  # Top 5 findings

    def _generate_strategic_recommendations(
        self,
        documents: list[ProcessedDocument],
        bmc: BusinessModelCanvas,
        vpc: ValuePropositionCanvas
    ) -> list[str]:
        """Generate strategic recommendations."""

        recommendations = []

        # BMC-based recommendations
        if not bmc.revenue_streams:
            recommendations.append("Develop clear revenue stream strategy to ensure business sustainability")

        if len(bmc.key_partners) == 0:
            recommendations.append("Identify strategic partnerships to enhance capabilities and market reach")

        if len(bmc.channels) < 2:
            recommendations.append("Diversify distribution channels to reduce market access risk")

        # VPC-based recommendations
        if len(vpc.pain_relievers) < len(vpc.pains):
            recommendations.append("Develop additional solutions to address all identified customer pain points")

        if len(vpc.gain_creators) < len(vpc.gains):
            recommendations.append("Create more value-add features to satisfy customer gain expectations")

        # Document analysis recommendations
        total_key_facts = sum(len(doc.key_facts) for doc in documents)
        if total_key_facts < 10:
            recommendations.append("Gather additional quantitative data to support strategic decisions")

        return recommendations[:5]  # Top 5 recommendations

    def _generate_implementation_roadmap(self, portfolio: InitiativePortfolio) -> str:
        """Generate implementation roadmap from initiative portfolio."""

        if not portfolio.initiatives:
            return "Implementation roadmap requires defined strategic initiatives."

        high_priority = portfolio.get_high_priority_initiatives()

        roadmap_sections = []

        # Phase 1: High Priority Initiatives
        if high_priority:
            phase1_items = [f"• {init.title}" for init in high_priority[:3]]
            roadmap_sections.append("Phase 1 (0-6 months): Critical Priorities\n" + "\n".join(phase1_items))

        # Phase 2: Medium Priority Initiatives
        medium_priority = [
            init for init in portfolio.initiatives
            if ((portfolio.scoring_method == "PIE" and init.pie_score and init.pie_score.priority_tier == "Medium") or
                (portfolio.scoring_method == "ICE" and init.ice_score and init.ice_score.priority_tier == "Medium"))
        ]

        if medium_priority:
            phase2_items = [f"• {init.title}" for init in medium_priority[:3]]
            roadmap_sections.append("Phase 2 (6-12 months): Supporting Initiatives\n" + "\n".join(phase2_items))

        # Phase 3: Long-term initiatives
        low_priority = [
            init for init in portfolio.initiatives
            if ((portfolio.scoring_method == "PIE" and init.pie_score and init.pie_score.priority_tier == "Low") or
                (portfolio.scoring_method == "ICE" and init.ice_score and init.ice_score.priority_tier == "Low"))
        ]

        if low_priority:
            phase3_items = [f"• {init.title}" for init in low_priority[:3]]
            roadmap_sections.append("Phase 3 (12+ months): Future Opportunities\n" + "\n".join(phase3_items))

        return "\n\n".join(roadmap_sections) if roadmap_sections else "Implementation roadmap requires initiative prioritization."

    def _generate_executive_summary(self, brief: StrategyBrief) -> str:
        """Generate executive summary from brief components."""

        summary_parts = []

        # Opening
        summary_parts.append(f"This strategic analysis examines {len(brief.evidence_sources)} source documents to provide actionable insights and recommendations.")

        # Key findings
        if brief.key_findings:
            summary_parts.append(f"Key findings include: {'; '.join(brief.key_findings[:2])}.")

        # Strategic focus
        if brief.business_model_canvas and brief.business_model_canvas.value_propositions:
            summary_parts.append(f"The strategy centers on {len(brief.business_model_canvas.value_propositions)} core value propositions targeting {len(brief.business_model_canvas.customer_segments)} market segments.")

        # Recommendations
        if brief.strategic_recommendations:
            summary_parts.append(f"Primary recommendations focus on: {'; '.join(brief.strategic_recommendations[:2])}.")

        # Implementation
        if brief.strategic_initiatives:
            summary_parts.append(f"Implementation involves {len(brief.strategic_initiatives)} strategic initiatives prioritized across multiple phases.")

        return " ".join(summary_parts)

    def _assess_evidence_strength(
        self,
        documents: list[ProcessedDocument],
        bmc: BusinessModelCanvas,
        vpc: ValuePropositionCanvas
    ) -> str:
        """Assess overall evidence strength."""

        doc_count = len(documents)
        total_sections = sum(len(doc.sections) for doc in documents)
        bmc_evidence = sum(len(sources) for sources in bmc.evidence_sources.values())
        vpc_evidence = sum(len(sources) for sources in vpc.evidence_sources.values())

        evidence_score = (doc_count * 2 + total_sections + bmc_evidence + vpc_evidence) / 20

        if evidence_score >= 1.0:
            return "Strong evidence base with comprehensive document coverage"
        elif evidence_score >= 0.5:
            return "Moderate evidence base - recommend additional sources"
        else:
            return "Limited evidence base - gather more supporting documentation"

    def _assess_confidence_level(
        self,
        documents: list[ProcessedDocument],
        bmc: BusinessModelCanvas,
        vpc: ValuePropositionCanvas
    ) -> str:
        """Assess confidence level in strategic analysis."""

        # Factor in multiple evidence dimensions
        completeness = len(bmc.evidence_sources) / 9  # 9 BMC sections
        evidence_diversity = len(set(sum(bmc.evidence_sources.values(), [])))
        vpc_fit = 1.0 if "Strong" in vpc.fit_assessment.get("overall_fit", "") else 0.5

        confidence_score = (completeness + evidence_diversity/10 + vpc_fit) / 3

        if confidence_score >= 0.75:
            return "High confidence - comprehensive analysis with strong evidence"
        elif confidence_score >= 0.5:
            return "Moderate confidence - good foundation with some gaps"
        else:
            return "Low confidence - requires additional validation and evidence"

    def _calculate_completeness_score(self, brief: StrategyBrief) -> float:
        """Calculate overall completeness score for the brief."""

        sections = [
            brief.executive_summary,
            brief.situation_analysis,
            brief.market_analysis,
            brief.competitive_landscape,
            brief.internal_capabilities,
            brief.implementation_roadmap
        ]

        filled_sections = sum(1 for section in sections if len(section) > 50)  # Minimum meaningful content
        section_score = filled_sections / len(sections)

        # Factor in framework completeness
        bmc_score = len(brief.business_model_canvas.evidence_sources) / 9 if brief.business_model_canvas else 0
        vpc_score = len(brief.value_proposition_canvas.evidence_sources) / 6 if brief.value_proposition_canvas else 0

        # Factor in recommendations and initiatives
        rec_score = min(1.0, len(brief.strategic_recommendations) / 3)
        init_score = min(1.0, len(brief.strategic_initiatives) / 5)

        overall_score = (section_score + bmc_score + vpc_score + rec_score + init_score) / 5
        return round(overall_score, 2)

    def _generate_success_metrics(self, bmc: BusinessModelCanvas, vpc: ValuePropositionCanvas) -> list[str]:
        """Generate success metrics based on strategic frameworks."""

        metrics = []

        # Revenue-focused metrics
        if bmc.revenue_streams:
            metrics.append("Revenue growth rate (quarterly)")
            metrics.append("Customer acquisition cost (CAC)")

        # Customer-focused metrics
        if bmc.customer_segments:
            metrics.append("Customer satisfaction score (NPS)")
            metrics.append("Customer retention rate")

        # Value proposition metrics
        if vpc.products_services:
            metrics.append("Product-market fit score")
            metrics.append("Feature adoption rates")

        # Operational metrics
        if bmc.key_activities:
            metrics.append("Operational efficiency metrics")
            metrics.append("Time-to-market for new initiatives")

        return metrics[:6]  # Top 6 metrics

    def _generate_risk_mitigation(self, documents: list[ProcessedDocument], brief: StrategyBrief) -> dict[str, str]:
        """Generate risk analysis and mitigation strategies."""

        risks = {}

        # Market risks
        if "market" in brief.market_analysis.lower():
            risks["Market Risk"] = "Monitor market trends and maintain strategy flexibility"

        # Competitive risks
        if "competitor" in brief.competitive_landscape.lower():
            risks["Competitive Risk"] = "Develop sustainable competitive advantages and barriers to entry"

        # Execution risks
        if brief.strategic_initiatives:
            risks["Execution Risk"] = "Implement robust project management and regular progress reviews"

        # Resource risks
        if brief.business_model_canvas and not brief.business_model_canvas.key_resources:
            risks["Resource Risk"] = "Secure critical resources and develop backup plans"

        return risks

    def _extract_assumptions(self, documents: list[ProcessedDocument], brief: StrategyBrief) -> list[str]:
        """Extract key assumptions underlying the strategy."""

        assumptions = []

        # Market assumptions
        if "growth" in brief.market_analysis.lower():
            assumptions.append("Market growth continues at projected rates")

        # Customer assumptions
        if brief.business_model_canvas and brief.business_model_canvas.customer_segments:
            assumptions.append("Customer segments remain stable and accessible")

        # Capability assumptions
        if brief.strategic_initiatives:
            assumptions.append("Organization has capacity to execute planned initiatives")

        # Competitive assumptions
        if "competition" in brief.competitive_landscape.lower():
            assumptions.append("Competitive landscape remains relatively stable")

        return assumptions[:5]  # Top 5 assumptions

    def _load_brief_template(self) -> Template:
        """Load Jinja2 template for strategy brief formatting."""

        template_str = """
# {{ title }}

**Version:** {{ version }}  
**Created:** {{ created_date }}  
**Authors:** {{ authors|join(', ') }}

## Executive Summary

{{ executive_summary }}

### Key Findings
{% for finding in key_findings %}
- {{ finding }}
{% endfor %}

### Strategic Recommendations
{% for rec in strategic_recommendations %}
- {{ rec }}
{% endfor %}

## Situation Analysis

{{ situation_analysis }}

## Market Analysis

{{ market_analysis }}

## Competitive Landscape

{{ competitive_landscape }}

## Internal Capabilities

{{ internal_capabilities }}

## Strategic Framework

### Business Model Canvas
{% if business_model_canvas %}
**Value Propositions:** {{ business_model_canvas.value_propositions|join('; ') }}  
**Customer Segments:** {{ business_model_canvas.customer_segments|join('; ') }}  
**Revenue Streams:** {{ business_model_canvas.revenue_streams|join('; ') }}
{% endif %}

### Value Proposition Canvas
{% if value_proposition_canvas %}
**Product-Market Fit:** {{ value_proposition_canvas.fit_assessment.overall_fit }}  
**Key Jobs:** {{ value_proposition_canvas.customer_jobs[:3]|join('; ') }}  
**Main Pains:** {{ value_proposition_canvas.pains[:3]|join('; ') }}
{% endif %}

## Implementation Roadmap

{{ implementation_roadmap }}

### Success Metrics
{% for metric in success_metrics %}
- {{ metric }}
{% endfor %}

## Risk Analysis & Mitigation

{% for risk, mitigation in risks_mitigation.items() %}
**{{ risk }}:** {{ mitigation }}  
{% endfor %}

## Key Assumptions

{% for assumption in assumptions %}
- {{ assumption }}
{% endfor %}

## Evidence Sources

{% for source in evidence_sources %}
- {{ source }}
{% endfor %}

---

**Quality Assessment:**  
- Evidence Strength: {{ evidence_strength }}  
- Confidence Level: {{ confidence_level }}  
- Completeness Score: {{ completeness_score }}
        """

        return Template(template_str.strip())

    def export_brief_markdown(self, brief: StrategyBrief) -> str:
        """Export strategy brief as Markdown."""
        return self.brief_template.render(**brief.dict())

    def export_brief_html(self, brief: StrategyBrief) -> str:
        """Export strategy brief as HTML."""
        import markdown
        md_content = self.export_brief_markdown(brief)
        return markdown.markdown(md_content, extensions=['tables', 'toc'])

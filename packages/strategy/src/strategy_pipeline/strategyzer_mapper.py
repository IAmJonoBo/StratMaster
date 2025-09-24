"""Strategyzer model mapping (Business Model Canvas, Value Proposition Canvas)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .document_processor import ProcessedDocument

logger = logging.getLogger(__name__)


class BusinessModelCanvas(BaseModel):
    """Business Model Canvas (BMC) structure following Strategyzer framework."""
    
    # Core sections of BMC
    key_partners: List[str] = Field(default_factory=list, description="Who are our key partners and suppliers?")
    key_activities: List[str] = Field(default_factory=list, description="What key activities does our value proposition require?")
    key_resources: List[str] = Field(default_factory=list, description="What key resources does our value proposition require?")
    
    value_propositions: List[str] = Field(default_factory=list, description="What value do we deliver to customers?")
    
    customer_relationships: List[str] = Field(default_factory=list, description="What type of relationship does each customer segment expect?")
    channels: List[str] = Field(default_factory=list, description="Through which channels do our customer segments want to be reached?")
    customer_segments: List[str] = Field(default_factory=list, description="For whom are we creating value?")
    
    cost_structure: List[str] = Field(default_factory=list, description="What are the most important costs inherent in our business model?")
    revenue_streams: List[str] = Field(default_factory=list, description="For what value are our customers really willing to pay?")
    
    # Additional metadata
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores for each section")
    evidence_sources: Dict[str, List[str]] = Field(default_factory=dict, description="Source documents for each section")


class ValuePropositionCanvas(BaseModel):
    """Value Proposition Canvas (VPC) structure following Strategyzer framework."""
    
    # Customer Profile (right side)
    customer_jobs: List[str] = Field(default_factory=list, description="What jobs is your customer trying to get done?")
    pains: List[str] = Field(default_factory=list, description="What pains do they experience?")
    gains: List[str] = Field(default_factory=list, description="What gains do they expect or desire?")
    
    # Value Map (left side)  
    products_services: List[str] = Field(default_factory=list, description="What products and services do you offer?")
    pain_relievers: List[str] = Field(default_factory=list, description="How do you relieve customer pains?")
    gain_creators: List[str] = Field(default_factory=list, description="How do you create customer gains?")
    
    # Analysis
    fit_assessment: Dict[str, str] = Field(default_factory=dict, description="Assessment of product-market fit")
    priority_ranking: Dict[str, int] = Field(default_factory=dict, description="Priority ranking of elements")
    evidence_sources: Dict[str, List[str]] = Field(default_factory=dict, description="Source documents for each section")


class StrategyzerMapper:
    """Maps processed documents to Strategyzer frameworks (BMC, VPC)."""
    
    def __init__(self):
        self.bmc_keywords = {
            'key_partners': [
                'partner', 'supplier', 'vendor', 'alliance', 'joint venture', 'collaboration',
                'distributor', 'reseller', 'affiliate', 'strategic partner'
            ],
            'key_activities': [
                'develop', 'produce', 'manufacture', 'design', 'research', 'marketing', 'sales',
                'platform', 'network', 'problem solving', 'production', 'service delivery'
            ],
            'key_resources': [
                'intellectual property', 'patent', 'brand', 'copyright', 'data', 'technology',
                'infrastructure', 'facilities', 'equipment', 'staff', 'expertise', 'capital'
            ],
            'value_propositions': [
                'value', 'benefit', 'solution', 'offering', 'proposition', 'advantage',
                'differentiator', 'unique', 'innovation', 'convenience', 'performance'
            ],
            'customer_relationships': [
                'relationship', 'service', 'support', 'community', 'personal', 'self-service',
                'automated', 'co-creation', 'dedicated', 'assistance'
            ],
            'channels': [
                'channel', 'distribution', 'retail', 'online', 'direct sales', 'website',
                'store', 'marketplace', 'partner channel', 'mobile app'
            ],
            'customer_segments': [
                'customer', 'segment', 'target', 'audience', 'user', 'client', 'demographic',
                'market', 'niche', 'persona', 'buyer'
            ],
            'cost_structure': [
                'cost', 'expense', 'fixed cost', 'variable cost', 'overhead', 'operational cost',
                'development cost', 'marketing cost', 'salary', 'rent', 'licensing'
            ],
            'revenue_streams': [
                'revenue', 'income', 'pricing', 'subscription', 'licensing', 'advertising',
                'commission', 'fee', 'transaction', 'recurring', 'one-time payment'
            ]
        }
        
        self.vpc_keywords = {
            'customer_jobs': [
                'job', 'task', 'need', 'requirement', 'goal', 'objective', 'problem to solve',
                'functional job', 'emotional job', 'social job'
            ],
            'pains': [
                'pain', 'problem', 'frustration', 'obstacle', 'challenge', 'risk', 'fear',
                'barrier', 'difficulty', 'annoyance', 'undesired outcome'
            ],
            'gains': [
                'gain', 'benefit', 'outcome', 'desire', 'want', 'expectation', 'requirement',
                'delight', 'surprise', 'social gain', 'positive outcome'
            ],
            'products_services': [
                'product', 'service', 'feature', 'offering', 'solution', 'tool', 'platform',
                'application', 'system', 'technology'
            ],
            'pain_relievers': [
                'solve', 'eliminate', 'reduce', 'avoid', 'prevent', 'mitigate', 'relieve',
                'address', 'fix', 'remove obstacle'
            ],
            'gain_creators': [
                'create', 'deliver', 'generate', 'provide', 'enable', 'increase', 'improve',
                'enhance', 'maximize', 'optimize'
            ]
        }
    
    def map_to_bmc(self, documents: List[ProcessedDocument]) -> BusinessModelCanvas:
        """Map processed documents to Business Model Canvas."""
        logger.info(f"Mapping {len(documents)} documents to Business Model Canvas")
        
        bmc = BusinessModelCanvas()
        evidence_sources = {}
        confidence_scores = {}
        
        # Process each document
        for doc in documents:
            doc_content = " ".join([section.content for section in doc.sections])
            doc_name = doc.filename
            
            # Map content to BMC sections
            for section_name, keywords in self.bmc_keywords.items():
                matches = self._find_keyword_matches(doc_content, keywords)
                
                if matches:
                    current_items = getattr(bmc, section_name)
                    
                    # Extract relevant sentences containing keywords
                    relevant_content = self._extract_relevant_sentences(doc_content, keywords)
                    
                    for content in relevant_content:
                        if content not in current_items:
                            current_items.append(content)
                    
                    # Track evidence sources
                    if section_name not in evidence_sources:
                        evidence_sources[section_name] = []
                    evidence_sources[section_name].append(doc_name)
                    
                    # Calculate confidence score based on keyword frequency
                    confidence = min(1.0, len(matches) / 10.0)  # Normalize to 0-1
                    confidence_scores[section_name] = max(
                        confidence_scores.get(section_name, 0.0), confidence
                    )
        
        bmc.evidence_sources = evidence_sources
        bmc.confidence_scores = confidence_scores
        
        logger.info(f"BMC mapping complete. Found content for {len(evidence_sources)} sections")
        return bmc
    
    def map_to_vpc(self, documents: List[ProcessedDocument]) -> ValuePropositionCanvas:
        """Map processed documents to Value Proposition Canvas."""
        logger.info(f"Mapping {len(documents)} documents to Value Proposition Canvas")
        
        vpc = ValuePropositionCanvas()
        evidence_sources = {}
        
        # Process each document
        for doc in documents:
            doc_content = " ".join([section.content for section in doc.sections])
            doc_name = doc.filename
            
            # Map content to VPC sections
            for section_name, keywords in self.vpc_keywords.items():
                matches = self._find_keyword_matches(doc_content, keywords)
                
                if matches:
                    current_items = getattr(vpc, section_name)
                    
                    # Extract relevant sentences
                    relevant_content = self._extract_relevant_sentences(doc_content, keywords)
                    
                    for content in relevant_content:
                        if content not in current_items:
                            current_items.append(content)
                    
                    # Track evidence sources
                    if section_name not in evidence_sources:
                        evidence_sources[section_name] = []
                    evidence_sources[section_name].append(doc_name)
        
        vpc.evidence_sources = evidence_sources
        
        # Perform fit assessment
        vpc.fit_assessment = self._assess_product_market_fit(vpc)
        vpc.priority_ranking = self._rank_vpc_elements(vpc)
        
        logger.info(f"VPC mapping complete. Found content for {len(evidence_sources)} sections")
        return vpc
    
    def _find_keyword_matches(self, text: str, keywords: List[str]) -> List[str]:
        """Find keyword matches in text."""
        text_lower = text.lower()
        matches = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches.append(keyword)
        
        return matches
    
    def _extract_relevant_sentences(self, text: str, keywords: List[str], max_sentences: int = 5) -> List[str]:
        """Extract sentences containing keywords."""
        import nltk
        
        sentences = nltk.sent_tokenize(text)
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence contains any keywords
            for keyword in keywords:
                if keyword.lower() in sentence_lower and len(sentence.split()) > 5:
                    # Clean and add sentence
                    clean_sentence = sentence.strip()
                    if clean_sentence not in relevant_sentences:
                        relevant_sentences.append(clean_sentence)
                    break
            
            if len(relevant_sentences) >= max_sentences:
                break
        
        return relevant_sentences
    
    def _assess_product_market_fit(self, vpc: ValuePropositionCanvas) -> Dict[str, str]:
        """Assess product-market fit based on VPC alignment."""
        fit_assessment = {}
        
        # Check alignment between customer profile and value map
        jobs_coverage = len(vpc.products_services) / max(len(vpc.customer_jobs), 1)
        pains_coverage = len(vpc.pain_relievers) / max(len(vpc.pains), 1)
        gains_coverage = len(vpc.gain_creators) / max(len(vpc.gains), 1)
        
        # Overall fit score
        overall_fit = (jobs_coverage + pains_coverage + gains_coverage) / 3
        
        if overall_fit >= 0.8:
            fit_level = "Strong Fit"
        elif overall_fit >= 0.5:
            fit_level = "Moderate Fit"
        else:
            fit_level = "Weak Fit"
        
        fit_assessment = {
            "overall_fit": fit_level,
            "jobs_coverage": f"{jobs_coverage:.2f}",
            "pains_coverage": f"{pains_coverage:.2f}", 
            "gains_coverage": f"{gains_coverage:.2f}",
            "recommendations": self._generate_fit_recommendations(jobs_coverage, pains_coverage, gains_coverage)
        }
        
        return fit_assessment
    
    def _generate_fit_recommendations(self, jobs_coverage: float, pains_coverage: float, gains_coverage: float) -> str:
        """Generate recommendations for improving product-market fit."""
        recommendations = []
        
        if jobs_coverage < 0.5:
            recommendations.append("Consider expanding product/service offerings to better address customer jobs")
        
        if pains_coverage < 0.5:
            recommendations.append("Develop more pain relievers to address customer frustrations")
        
        if gains_coverage < 0.5:
            recommendations.append("Create additional gain creators to enhance customer value")
        
        if not recommendations:
            recommendations.append("Strong alignment between customer profile and value proposition")
        
        return "; ".join(recommendations)
    
    def _rank_vpc_elements(self, vpc: ValuePropositionCanvas) -> Dict[str, int]:
        """Rank VPC elements by importance (simplified heuristic)."""
        priority_ranking = {}
        
        # Simple ranking based on length/detail (more detail = higher priority)
        sections = ['customer_jobs', 'pains', 'gains', 'products_services', 'pain_relievers', 'gain_creators']
        
        for section in sections:
            items = getattr(vpc, section)
            # Rank by average length of items (proxy for detail/importance)
            if items:
                avg_length = sum(len(item.split()) for item in items) / len(items)
                priority_ranking[section] = int(avg_length)
            else:
                priority_ranking[section] = 0
        
        return priority_ranking
    
    def generate_canvas_summary(self, bmc: BusinessModelCanvas, vpc: ValuePropositionCanvas) -> Dict[str, Any]:
        """Generate comprehensive summary of both canvases."""
        summary = {
            "bmc_completeness": self._calculate_bmc_completeness(bmc),
            "vpc_fit_score": vpc.fit_assessment.get("overall_fit", "Unknown"),
            "key_insights": self._extract_key_insights(bmc, vpc),
            "recommendations": self._generate_strategic_recommendations(bmc, vpc),
            "evidence_strength": self._assess_evidence_strength(bmc, vpc)
        }
        
        return summary
    
    def _calculate_bmc_completeness(self, bmc: BusinessModelCanvas) -> float:
        """Calculate how complete the BMC is (0-1 score)."""
        sections = [
            'key_partners', 'key_activities', 'key_resources', 'value_propositions',
            'customer_relationships', 'channels', 'customer_segments', 'cost_structure', 'revenue_streams'
        ]
        
        filled_sections = sum(1 for section in sections if getattr(bmc, section))
        return filled_sections / len(sections)
    
    def _extract_key_insights(self, bmc: BusinessModelCanvas, vpc: ValuePropositionCanvas) -> List[str]:
        """Extract key strategic insights from the canvases."""
        insights = []
        
        # BMC insights
        if len(bmc.value_propositions) > 3:
            insights.append("Multiple value propositions may indicate broad market appeal or lack of focus")
        
        if len(bmc.customer_segments) == 1:
            insights.append("Single customer segment suggests focused niche strategy")
        elif len(bmc.customer_segments) > 4:
            insights.append("Multiple customer segments may require diverse go-to-market strategies")
        
        # VPC insights
        fit_level = vpc.fit_assessment.get("overall_fit", "")
        if "Strong" in fit_level:
            insights.append("Strong product-market fit indicated by aligned customer profile and value map")
        elif "Weak" in fit_level:
            insights.append("Weak product-market fit suggests need for value proposition refinement")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _generate_strategic_recommendations(self, bmc: BusinessModelCanvas, vpc: ValuePropositionCanvas) -> List[str]:
        """Generate strategic recommendations based on canvas analysis."""
        recommendations = []
        
        # Check for missing critical elements
        if not bmc.revenue_streams:
            recommendations.append("Define clear revenue streams to ensure business sustainability")
        
        if not bmc.key_resources:
            recommendations.append("Identify key resources required to deliver value proposition")
        
        if len(vpc.pain_relievers) < len(vpc.pains):
            recommendations.append("Develop additional pain relievers to address all identified customer pains")
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _assess_evidence_strength(self, bmc: BusinessModelCanvas, vpc: ValuePropositionCanvas) -> str:
        """Assess strength of evidence supporting the canvases."""
        bmc_sources = sum(len(sources) for sources in bmc.evidence_sources.values())
        vpc_sources = sum(len(sources) for sources in vpc.evidence_sources.values())
        
        total_sources = bmc_sources + vpc_sources
        
        if total_sources >= 10:
            return "Strong evidence base with multiple document sources"
        elif total_sources >= 5:
            return "Moderate evidence base - consider additional sources"
        else:
            return "Limited evidence base - gather more supporting documents"
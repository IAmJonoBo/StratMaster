"""
Industry-Specific Strategy Templates for StratMaster

This module provides industry-specific strategy templates including:
- Template catalog with metadata
- Industry-specific KPIs and metrics
- Vertical-specific Jinja templates
- Template validation and management
"""

import os
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from jinja2 import Template
from pydantic import BaseModel, Field

# Feature flag for industry templates
ENABLE_INDUSTRY_TEMPLATES = os.getenv("ENABLE_INDUSTRY_TEMPLATES", "false").lower() == "true"


class IndustryVertical(str, Enum):
    """Industry verticals supported by StratMaster."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare" 
    FINTECH = "fintech"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    CONSULTING = "consulting"
    MEDIA = "media"
    AUTOMOTIVE = "automotive"
    ENERGY = "energy"
    REAL_ESTATE = "real_estate"
    GENERIC = "generic"  # Default fallback


class TemplateMetadata(BaseModel):
    """Metadata for industry strategy templates."""
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    industry: IndustryVertical
    name: str
    description: str
    version: str = "1.0"
    created_by: str = "StratMaster"
    tags: List[str] = Field(default_factory=list)
    recommended_kpis: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    common_challenges: List[str] = Field(default_factory=list)
    strategic_focus_areas: List[str] = Field(default_factory=list)


class IndustryTemplate(BaseModel):
    """Complete industry-specific strategy template."""
    metadata: TemplateMetadata
    template_content: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    sample_data: Dict[str, Any] = Field(default_factory=dict)


class IndustryTemplateManager:
    """Manages industry-specific strategy templates."""
    
    def __init__(self):
        self.templates: Dict[IndustryVertical, IndustryTemplate] = {}
        self.enabled = ENABLE_INDUSTRY_TEMPLATES
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default industry templates."""
        
        # Technology/SaaS Template
        tech_template = IndustryTemplate(
            metadata=TemplateMetadata(
                industry=IndustryVertical.TECHNOLOGY,
                name="Technology Strategy Template",
                description="Strategic framework for technology and SaaS companies",
                tags=["technology", "saas", "innovation", "scalability"],
                recommended_kpis=[
                    "Monthly Recurring Revenue (MRR)",
                    "Customer Acquisition Cost (CAC)",
                    "Customer Lifetime Value (CLV)",
                    "Monthly Active Users (MAU)",
                    "Feature Adoption Rate",
                    "Net Promoter Score (NPS)",
                    "Churn Rate",
                    "Developer Velocity"
                ],
                success_metrics=[
                    "Product-market fit score > 4.0",
                    "Monthly growth rate > 10%",
                    "CAC payback period < 12 months",
                    "Net Revenue Retention > 110%"
                ],
                common_challenges=[
                    "Scaling engineering teams efficiently",
                    "Maintaining product quality during rapid growth", 
                    "Customer onboarding and retention",
                    "Technical debt management",
                    "Market saturation and differentiation"
                ],
                strategic_focus_areas=[
                    "Product Innovation & R&D",
                    "Customer Experience & Success",
                    "Scalable Technology Architecture",
                    "Go-to-Market Strategy",
                    "Talent Acquisition & Retention"
                ]
            ),
            template_content=self._get_tech_template(),
            variables={
                "focus_on_scalability": True,
                "emphasize_innovation": True,
                "include_technical_metrics": True
            }
        )
        self.templates[IndustryVertical.TECHNOLOGY] = tech_template
        self.templates[IndustryVertical.SAAS] = tech_template  # Same template
        
        # Healthcare Template
        healthcare_template = IndustryTemplate(
            metadata=TemplateMetadata(
                industry=IndustryVertical.HEALTHCARE,
                name="Healthcare Strategy Template",
                description="Strategic framework for healthcare and life sciences companies",
                tags=["healthcare", "compliance", "patient-outcomes", "regulatory"],
                recommended_kpis=[
                    "Patient Satisfaction Score",
                    "Clinical Outcome Metrics",
                    "Regulatory Compliance Rate",
                    "Time-to-Market (Drug/Device)",
                    "Cost Per Patient Outcome",
                    "Provider Adoption Rate",
                    "Quality-Adjusted Life Years (QALY)",
                    "Revenue Per Patient"
                ],
                success_metrics=[
                    "Clinical trial success rate > 70%",
                    "FDA approval time < industry average",
                    "Patient safety incidents = 0",
                    "Compliance audit score > 95%"
                ],
                common_challenges=[
                    "Regulatory compliance and approval processes",
                    "Patient privacy and data security (HIPAA)",
                    "Clinical trial management and costs",
                    "Reimbursement and payer relations",
                    "Healthcare provider adoption"
                ],
                strategic_focus_areas=[
                    "Regulatory Strategy & Compliance",
                    "Clinical Evidence Generation",
                    "Patient Access & Outcomes",
                    "Healthcare Ecosystem Partnerships",
                    "Value-Based Care Models"
                ]
            ),
            template_content=self._get_healthcare_template(),
            variables={
                "focus_on_compliance": True,
                "emphasize_outcomes": True,
                "include_regulatory_metrics": True
            }
        )
        self.templates[IndustryVertical.HEALTHCARE] = healthcare_template
        
        # Fintech Template
        fintech_template = IndustryTemplate(
            metadata=TemplateMetadata(
                industry=IndustryVertical.FINTECH,
                name="Fintech Strategy Template", 
                description="Strategic framework for financial technology companies",
                tags=["fintech", "financial-services", "compliance", "security"],
                recommended_kpis=[
                    "Assets Under Management (AUM)",
                    "Transaction Volume",
                    "Customer Acquisition Cost (CAC)",
                    "Average Revenue Per User (ARPU)",
                    "Regulatory Compliance Score",
                    "Security Incident Rate",
                    "API Uptime (SLA)",
                    "Time to Settlement"
                ],
                success_metrics=[
                    "Regulatory compliance score > 98%",
                    "Security audit pass rate = 100%",
                    "Transaction success rate > 99.9%",
                    "Customer trust score > 4.5/5"
                ],
                common_challenges=[
                    "Financial regulations and compliance",
                    "Cybersecurity and fraud prevention",
                    "Trust and customer adoption",
                    "Integration with legacy financial systems",
                    "Capital requirements and funding"
                ],
                strategic_focus_areas=[
                    "Regulatory Compliance & Risk Management",
                    "Security & Fraud Prevention",
                    "Customer Trust & Experience",
                    "Financial Infrastructure & Partnerships",
                    "Product Innovation & Market Expansion"
                ]
            ),
            template_content=self._get_fintech_template(),
            variables={
                "focus_on_security": True,
                "emphasize_compliance": True,
                "include_financial_metrics": True
            }
        )
        self.templates[IndustryVertical.FINTECH] = fintech_template
        
        # Retail/E-commerce Template
        retail_template = IndustryTemplate(
            metadata=TemplateMetadata(
                industry=IndustryVertical.RETAIL,
                name="Retail Strategy Template",
                description="Strategic framework for retail and e-commerce companies",
                tags=["retail", "ecommerce", "customer-experience", "omnichannel"],
                recommended_kpis=[
                    "Same-Store Sales Growth",
                    "Gross Margin",
                    "Inventory Turnover",
                    "Customer Lifetime Value",
                    "Conversion Rate",
                    "Average Order Value (AOV)",
                    "Return Rate",
                    "Net Promoter Score (NPS)"
                ],
                success_metrics=[
                    "Year-over-year sales growth > 15%",
                    "Customer retention rate > 80%",
                    "Inventory turnover > 6x annually",
                    "Omnichannel customer satisfaction > 4.2/5"
                ],
                common_challenges=[
                    "Omnichannel customer experience",
                    "Inventory management and forecasting",
                    "Supply chain optimization", 
                    "Digital transformation and e-commerce",
                    "Customer personalization and retention"
                ],
                strategic_focus_areas=[
                    "Customer Experience & Personalization",
                    "Omnichannel Integration",
                    "Supply Chain Excellence",
                    "Digital Commerce Capabilities",
                    "Brand Positioning & Marketing"
                ]
            ),
            template_content=self._get_retail_template(),
            variables={
                "focus_on_experience": True,
                "emphasize_omnichannel": True,
                "include_retail_metrics": True
            }
        )
        self.templates[IndustryVertical.RETAIL] = retail_template
        self.templates[IndustryVertical.ECOMMERCE] = retail_template  # Same template
        
        # Generic/Default Template  
        generic_template = IndustryTemplate(
            metadata=TemplateMetadata(
                industry=IndustryVertical.GENERIC,
                name="Generic Strategy Template",
                description="Universal strategic framework for any industry",
                tags=["generic", "universal", "adaptable"],
                recommended_kpis=[
                    "Revenue Growth Rate",
                    "Market Share",
                    "Customer Satisfaction",
                    "Operational Efficiency",
                    "Profitability Margin",
                    "Employee Engagement",
                    "Brand Awareness",
                    "Innovation Index"
                ],
                success_metrics=[
                    "Revenue growth > 10% annually",
                    "Customer satisfaction > 4.0/5",
                    "Market share growth",
                    "Operational cost reduction"
                ],
                common_challenges=[
                    "Market competition and differentiation",
                    "Operational efficiency and cost management",
                    "Customer acquisition and retention",
                    "Talent recruitment and development",
                    "Technology adoption and digital transformation"
                ],
                strategic_focus_areas=[
                    "Market Position & Competitive Advantage",
                    "Customer Value & Experience",
                    "Operational Excellence",
                    "Innovation & Growth",
                    "Organizational Capabilities"
                ]
            ),
            template_content=self._get_generic_template(),
            variables={}
        )
        self.templates[IndustryVertical.GENERIC] = generic_template
    
    def get_template(self, industry: IndustryVertical) -> IndustryTemplate:
        """Get template for specified industry."""
        if not self.enabled:
            return self.templates[IndustryVertical.GENERIC]
        
        return self.templates.get(industry, self.templates[IndustryVertical.GENERIC])
    
    def get_available_industries(self) -> List[IndustryVertical]:
        """Get list of available industry templates."""
        if not self.enabled:
            return [IndustryVertical.GENERIC]
        
        return list(self.templates.keys())
    
    def get_industry_kpis(self, industry: IndustryVertical) -> List[str]:
        """Get recommended KPIs for industry."""
        template = self.get_template(industry)
        return template.metadata.recommended_kpis
    
    def render_strategy_template(
        self, 
        industry: IndustryVertical, 
        context: Dict[str, Any]
    ) -> str:
        """Render industry-specific strategy template with context."""
        template = self.get_template(industry)
        
        # Merge template variables with context
        render_context = {**template.variables, **context}
        
        # Add industry-specific data
        render_context.update({
            "industry": industry.value,
            "industry_name": industry.value.replace('_', ' ').title(),
            "recommended_kpis": template.metadata.recommended_kpis,
            "success_metrics": template.metadata.success_metrics,
            "common_challenges": template.metadata.common_challenges,
            "strategic_focus_areas": template.metadata.strategic_focus_areas,
        })
        
        jinja_template = Template(template.template_content)
        return jinja_template.render(**render_context)
    
    def _get_tech_template(self) -> str:
        """Technology industry template."""
        return """
# {{ title }} - Technology Strategy Brief

**Industry:** {{ industry_name }}  
**Version:** {{ version }}  
**Created:** {{ created_date }}  
**Authors:** {{ authors|join(', ') }}

## Executive Summary

{{ executive_summary }}

### Key Technology Findings
{% for finding in key_findings %}
- {{ finding }}
{% endfor %}

### Strategic Technology Recommendations  
{% for rec in strategic_recommendations %}
- {{ rec }}
{% endfor %}

## Technology Market Analysis

{{ market_analysis }}

### Key Technology Trends
- Cloud-first architecture and scalability
- AI/ML integration opportunities  
- Developer experience optimization
- Security and compliance automation

## Product-Market Fit Analysis

{{ situation_analysis }}

### Scalability Considerations
- Engineering team scaling strategies
- Technical architecture decisions
- Performance and reliability requirements
- Security and compliance frameworks

## Technology Competitive Landscape

{{ competitive_landscape }}

### Differentiation Factors
- Unique technology capabilities
- Developer and user experience
- Integration ecosystem
- Technical performance metrics

## Internal Technology Capabilities

{{ internal_capabilities }}

### Technical Infrastructure Assessment
- Current technology stack evaluation
- Development team capabilities
- DevOps and deployment maturity
- Security and monitoring capabilities

## Strategic Technology Initiatives

### Recommended KPIs
{% for kpi in recommended_kpis %}
- {{ kpi }}
{% endfor %}

### Success Metrics
{% for metric in success_metrics %}  
- {{ metric }}
{% endfor %}

### Technology Roadmap
{{ implementation_roadmap }}

## Risk Assessment & Mitigation

### Common Technology Challenges
{% for challenge in common_challenges %}
- {{ challenge }}
{% endfor %}

### Strategic Focus Areas
{% for area in strategic_focus_areas %}
- {{ area }}
{% endfor %}

## Supporting Evidence & Assumptions

**Evidence Sources:** {{ evidence_sources|join(', ') }}

**Key Assumptions:**
{% for assumption in assumptions %}
- {{ assumption }}
{% endfor %}

**Quality Assessment:**
- Evidence Strength: {{ evidence_strength }}
- Confidence Level: {{ confidence_level }}
- Completeness Score: {{ completeness_score }}

---
*Generated by StratMaster Technology Strategy Template v{{ version }}*
""".strip()

    def _get_healthcare_template(self) -> str:
        """Healthcare industry template."""
        return """
# {{ title }} - Healthcare Strategy Brief

**Industry:** {{ industry_name }}  
**Version:** {{ version }}  
**Created:** {{ created_date }}  
**Authors:** {{ authors|join(', ') }}

## Executive Summary

{{ executive_summary }}

### Key Healthcare Findings
{% for finding in key_findings %}
- {{ finding }}
{% endfor %}

### Strategic Healthcare Recommendations  
{% for rec in strategic_recommendations %}
- {{ rec }}
{% endfor %}

## Healthcare Market Analysis

{{ market_analysis }}

### Healthcare Trends & Regulations
- Value-based care model adoption
- Digital health technology integration
- Regulatory compliance requirements (FDA, HIPAA)
- Patient outcome measurement standards

## Clinical & Market Situation Analysis

{{ situation_analysis }}

### Patient Outcome Considerations
- Clinical efficacy requirements
- Patient safety protocols
- Quality assurance frameworks
- Healthcare provider adoption strategies

## Healthcare Competitive Landscape

{{ competitive_landscape }}

### Clinical Differentiation Factors
- Clinical evidence and outcomes
- Regulatory approval status
- Healthcare provider relationships
- Patient access and affordability

## Healthcare Capabilities Assessment  

{{ internal_capabilities }}

### Clinical Infrastructure Assessment
- Clinical research capabilities
- Regulatory affairs expertise
- Quality assurance systems
- Healthcare partnership network

## Strategic Healthcare Initiatives

### Recommended Healthcare KPIs
{% for kpi in recommended_kpis %}
- {{ kpi }}
{% endfor %}

### Clinical Success Metrics
{% for metric in success_metrics %}  
- {{ metric }}
{% endfor %}

### Implementation Roadmap
{{ implementation_roadmap }}

## Healthcare Risk Assessment

### Common Healthcare Challenges
{% for challenge in common_challenges %}
- {{ challenge }}
{% endfor %}

### Strategic Focus Areas
{% for area in strategic_focus_areas %}
- {{ area }}
{% endfor %}

## Clinical Evidence & Regulatory Assumptions

**Evidence Sources:** {{ evidence_sources|join(', ') }}

**Key Clinical Assumptions:**
{% for assumption in assumptions %}
- {{ assumption }}
{% endfor %}

**Quality Assessment:**
- Evidence Strength: {{ evidence_strength }}
- Confidence Level: {{ confidence_level }}
- Completeness Score: {{ completeness_score }}

---
*Generated by StratMaster Healthcare Strategy Template v{{ version }}*
""".strip()

    def _get_fintech_template(self) -> str:
        """Fintech industry template."""
        return """
# {{ title }} - Fintech Strategy Brief

**Industry:** {{ industry_name }}  
**Version:** {{ version }}  
**Created:** {{ created_date }}  
**Authors:** {{ authors|join(', ') }}

## Executive Summary

{{ executive_summary }}

### Key Fintech Findings
{% for finding in key_findings %}
- {{ finding }}
{% endfor %}

### Strategic Fintech Recommendations  
{% for rec in strategic_recommendations %}
- {{ rec }}
{% endfor %}

## Financial Services Market Analysis

{{ market_analysis }}

### Fintech Trends & Regulations
- Open banking and API standards
- Regulatory compliance (PCI DSS, SOX, AML)
- Digital payment innovation
- Cryptocurrency and blockchain integration

## Financial Product-Market Analysis

{{ situation_analysis }}

### Financial Services Considerations
- Customer trust and security requirements
- Regulatory compliance frameworks
- Financial infrastructure integration
- Risk management and fraud prevention

## Fintech Competitive Landscape

{{ competitive_landscape }}

### Financial Services Differentiation
- Security and compliance standards
- Financial product innovation
- Customer experience and trust
- Integration capabilities

## Financial Infrastructure Capabilities

{{ internal_capabilities }}

### Fintech Infrastructure Assessment
- Financial systems integration
- Security and compliance capabilities
- Risk management frameworks
- Regulatory affairs expertise

## Strategic Fintech Initiatives

### Recommended Financial KPIs
{% for kpi in recommended_kpis %}
- {{ kpi }}
{% endfor %}

### Financial Success Metrics
{% for metric in success_metrics %}  
- {{ metric }}
{% endfor %}

### Implementation Roadmap
{{ implementation_roadmap }}

## Financial Risk Assessment

### Common Fintech Challenges
{% for challenge in common_challenges %}
- {{ challenge }}
{% endfor %}

### Strategic Focus Areas
{% for area in strategic_focus_areas %}
- {{ area }}
{% endfor %}

## Financial Evidence & Compliance Assumptions

**Evidence Sources:** {{ evidence_sources|join(', ') }}

**Key Financial Assumptions:**
{% for assumption in assumptions %}
- {{ assumption }}
{% endfor %}

**Quality Assessment:**
- Evidence Strength: {{ evidence_strength }}
- Confidence Level: {{ confidence_level }}
- Completeness Score: {{ completeness_score }}

---
*Generated by StratMaster Fintech Strategy Template v{{ version }}*
""".strip()

    def _get_retail_template(self) -> str:
        """Retail industry template."""
        return """
# {{ title }} - Retail Strategy Brief

**Industry:** {{ industry_name }}  
**Version:** {{ version }}  
**Created:** {{ created_date }}  
**Authors:** {{ authors|join(', ') }}

## Executive Summary

{{ executive_summary }}

### Key Retail Findings
{% for finding in key_findings %}
- {{ finding }}
{% endfor %}

### Strategic Retail Recommendations  
{% for rec in strategic_recommendations %}
- {{ rec }}
{% endfor %}

## Retail Market Analysis

{{ market_analysis }}

### Retail Trends & Consumer Behavior
- Omnichannel customer experience expectations
- Digital commerce transformation
- Supply chain optimization
- Personalization and customer data analytics

## Customer & Market Situation

{{ situation_analysis }}

### Customer Experience Considerations
- Omnichannel integration requirements
- Customer journey optimization
- Personalization and recommendation systems
- Inventory and fulfillment strategies

## Retail Competitive Landscape

{{ competitive_landscape }}

### Retail Differentiation Factors
- Customer experience and service
- Product assortment and pricing
- Brand positioning and loyalty
- Omnichannel capabilities

## Retail Operations Capabilities

{{ internal_capabilities }}

### Retail Infrastructure Assessment
- Store operations and management
- E-commerce platform capabilities
- Supply chain and logistics
- Customer data and analytics systems

## Strategic Retail Initiatives

### Recommended Retail KPIs
{% for kpi in recommended_kpis %}
- {{ kpi }}
{% endfor %}

### Retail Success Metrics
{% for metric in success_metrics %}  
- {{ metric }}
{% endfor %}

### Implementation Roadmap
{{ implementation_roadmap }}

## Retail Risk Assessment

### Common Retail Challenges
{% for challenge in common_challenges %}
- {{ challenge }}
{% endfor %}

### Strategic Focus Areas
{% for area in strategic_focus_areas %}
- {{ area }}
{% endfor %}

## Retail Evidence & Market Assumptions

**Evidence Sources:** {{ evidence_sources|join(', ') }}

**Key Retail Assumptions:**
{% for assumption in assumptions %}
- {{ assumption }}
{% endfor %}

**Quality Assessment:**
- Evidence Strength: {{ evidence_strength }}
- Confidence Level: {{ confidence_level }}
- Completeness Score: {{ completeness_score }}

---
*Generated by StratMaster Retail Strategy Template v{{ version }}*
""".strip()

    def _get_generic_template(self) -> str:
        """Generic industry template (fallback)."""
        return """
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

## Market Analysis

{{ market_analysis }}

## Situation Analysis

{{ situation_analysis }}

## Competitive Landscape

{{ competitive_landscape }}

## Internal Capabilities

{{ internal_capabilities }}

## Strategic Initiatives

### Recommended KPIs
{% for kpi in recommended_kpis %}
- {{ kpi }}
{% endfor %}

### Success Metrics
{% for metric in success_metrics %}  
- {{ metric }}
{% endfor %}

### Implementation Roadmap
{{ implementation_roadmap }}

## Risk Assessment

### Common Challenges
{% for challenge in common_challenges %}
- {{ challenge }}
{% endfor %}

### Strategic Focus Areas
{% for area in strategic_focus_areas %}
- {{ area }}
{% endfor %}

## Supporting Evidence

**Evidence Sources:** {{ evidence_sources|join(', ') }}

**Key Assumptions:**
{% for assumption in assumptions %}
- {{ assumption }}
{% endfor %}

**Quality Assessment:**
- Evidence Strength: {{ evidence_strength }}
- Confidence Level: {{ confidence_level }}
- Completeness Score: {{ completeness_score }}

---
*Generated by StratMaster Generic Strategy Template v{{ version }}*
""".strip()


# Global template manager instance
template_manager = IndustryTemplateManager()


# Convenience functions for API integration
def get_available_industries() -> List[str]:
    """Get list of available industry templates."""
    return [industry.value for industry in template_manager.get_available_industries()]


def get_industry_template(industry: str) -> Dict[str, Any]:
    """Get industry template metadata."""
    try:
        industry_enum = IndustryVertical(industry)
    except ValueError:
        industry_enum = IndustryVertical.GENERIC
    
    template = template_manager.get_template(industry_enum)
    
    return {
        "template_id": template.metadata.template_id,
        "industry": template.metadata.industry,
        "name": template.metadata.name,
        "description": template.metadata.description,
        "recommended_kpis": template.metadata.recommended_kpis,
        "success_metrics": template.metadata.success_metrics,
        "common_challenges": template.metadata.common_challenges,
        "strategic_focus_areas": template.metadata.strategic_focus_areas,
        "enabled": template_manager.enabled
    }


def get_industry_kpis(industry: str) -> List[str]:
    """Get recommended KPIs for industry."""
    try:
        industry_enum = IndustryVertical(industry)
    except ValueError:
        industry_enum = IndustryVertical.GENERIC
    
    return template_manager.get_industry_kpis(industry_enum)


def render_industry_strategy(
    industry: str,
    strategy_data: Dict[str, Any]
) -> str:
    """Render strategy using industry-specific template."""
    try:
        industry_enum = IndustryVertical(industry)
    except ValueError:
        industry_enum = IndustryVertical.GENERIC
    
    return template_manager.render_strategy_template(industry_enum, strategy_data)
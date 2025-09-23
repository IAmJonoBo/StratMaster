---
title: Your First Strategy Analysis
description: Build a complete strategic analysis using StratMaster's multi-agent system
version: 0.1.0
platform: Python 3.11+
nav_order: 2
parent: Tutorials
---

# Your First Strategy Analysis

This tutorial walks you through creating a complete strategic analysis using StratMaster's multi-agent debate system. You'll learn how to orchestrate research, validation, and recommendation generation for a real business scenario.

## Prerequisites

- Complete the [Quick Start Tutorial](quickstart.md)
- StratMaster API server running on `http://127.0.0.1:8080`
- Basic understanding of JSON and REST APIs

## Scenario: Digital Transformation Strategy

We'll analyze a strategic question: **"Should our B2B SaaS company invest in AI-powered customer support?"**

This scenario demonstrates:
- Multi-step research planning
- Evidence collection and validation  
- Multi-agent debate for fact-checking
- Strategic recommendation synthesis
- Quality evaluation gates

## Step 1: Define the Strategic Context

First, let's establish the business context with a Customer Episode Profile (CEP) and Jobs-to-be-Done (JTBD):

```bash
# Create a strategic experiment  
curl -X POST http://127.0.0.1:8080/experiments \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-001" \
  -d '{
    "tenant_id": "tutorial-company",
    "title": "AI Customer Support Investment Analysis",
    "hypothesis": "AI-powered support will reduce costs by 30% while improving customer satisfaction",
    "success_metrics": [
      "Customer satisfaction score > 4.5/5",
      "Support ticket resolution time < 4 hours",
      "Support cost per ticket < $15"
    ],
    "duration_weeks": 12,
    "confidence_threshold": 0.75
  }'
```

**Expected response:**
```json
{
  "experiment_id": "exp-ai-support-001",
  "tenant_id": "tutorial-company",
  "status": "planned",
  "created_at": "2024-01-18T10:00:00Z",
  "hypothesis_confidence": 0.6,
  "risk_factors": [
    "Implementation complexity",
    "Customer adoption curve", 
    "Integration challenges"
  ]
}
```

## Step 2: Comprehensive Research Planning

Create a multi-faceted research plan covering technology, market, and business aspects:

```bash
curl -X POST http://127.0.0.1:8080/research/plan \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-002" \
  -d '{
    "query": "AI customer support ROI implementation challenges B2B SaaS 2024",
    "tenant_id": "tutorial-company", 
    "max_sources": 8,
    "research_depth": "comprehensive",
    "focus_areas": [
      "technology_readiness",
      "market_adoption", 
      "financial_impact",
      "implementation_risk",
      "competitive_landscape"
    ]
  }'
```

**Response includes expanded task breakdown:**
```json
{
  "plan_id": "plan-comprehensive-001",
  "tenant_id": "tutorial-company",
  "tasks": [
    {
      "id": "task-tech-1",
      "type": "technology_analysis", 
      "query": "AI chatbot accuracy rates enterprise implementation",
      "priority": "high",
      "estimated_duration_minutes": 20
    },
    {
      "id": "task-market-1", 
      "type": "market_research",
      "query": "B2B SaaS customer support automation adoption 2024",
      "priority": "high",
      "estimated_duration_minutes": 25
    },
    {
      "id": "task-financial-1",
      "type": "financial_analysis",
      "query": "customer support automation cost savings ROI studies", 
      "priority": "medium",
      "estimated_duration_minutes": 15
    }
  ],
  "estimated_total_duration_minutes": 85
}
```

## Step 3: Execute Research with Evidence Collection

Run the comprehensive research plan:

```bash  
curl -X POST http://127.0.0.1:8080/research/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-003" \
  -d '{
    "plan_id": "plan-comprehensive-001",
    "tenant_id": "tutorial-company",
    "evidence_standards": {
      "min_sources_per_claim": 2,
      "credibility_threshold": 0.7,
      "recency_weight": 0.8
    }
  }'
```

**Response provides structured claims with evidence:**
```json
{
  "session_id": "session-comprehensive-001", 
  "tenant_id": "tutorial-company",
  "claims": [
    {
      "id": "claim-cost-reduction",
      "text": "AI customer support systems reduce operational costs by 25-40% within 12 months",
      "confidence": 0.87,
      "evidence_count": 4,
      "source_ids": ["src-gartner-2024", "src-forrester-ai", "src-mckinsey-automation"]
    },
    {
      "id": "claim-customer-satisfaction",  
      "text": "Customer satisfaction scores improve by 15-20% with properly implemented AI support",
      "confidence": 0.82,
      "evidence_count": 3,
      "source_ids": ["src-zendesk-study", "src-salesforce-report"]
    },
    {
      "id": "claim-implementation-time",
      "text": "Enterprise AI support deployment typically requires 6-9 months for full implementation",
      "confidence": 0.79,
      "evidence_count": 2, 
      "source_ids": ["src-implementation-study", "src-vendor-timelines"]
    }
  ],
  "evidence": [
    {
      "text": "Enterprise study of 500 companies showed 32% average cost reduction after AI support deployment",
      "source_id": "src-gartner-2024",
      "url": "https://example.com/gartner-ai-support-2024",
      "relevance_score": 0.95,
      "credibility_score": 0.91,
      "publication_date": "2024-01-10"
    }
  ],
  "assumptions": [
    {
      "id": "assume-integration",  
      "text": "Existing CRM and ticketing systems can integrate with AI platforms",
      "confidence": 0.75,
      "requires_validation": true
    }
  ]
}
```

## Step 4: Multi-Agent Debate Validation

Now validate the research findings using multi-agent debate to catch biases and strengthen conclusions:

```bash
curl -X POST http://127.0.0.1:8080/debate/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-004" \
  -d '{
    "session_id": "session-comprehensive-001",
    "tenant_id": "tutorial-company",
    "claims": [
      {
        "id": "claim-cost-reduction",
        "text": "AI customer support systems reduce operational costs by 25-40% within 12 months", 
        "confidence": 0.87,
        "evidence_ids": ["evidence-1", "evidence-2", "evidence-3"]
      }
    ],
    "debate_config": {
      "max_rounds": 3,
      "agents": ["strategist", "critic", "adversary"],
      "consensus_threshold": 0.8
    }
  }'
```

**Response shows multi-agent validation:**
```json
{
  "debate_id": "debate-ai-support-001",
  "tenant_id": "tutorial-company", 
  "rounds": [
    {
      "round": 0,
      "agent": "strategist",
      "position": "The 25-40% cost reduction claim is well-supported by multiple enterprise studies",
      "confidence": 0.87,
      "supporting_evidence": ["src-gartner-2024", "src-forrester-ai"]
    },
    {
      "round": 1,
      "agent": "critic",
      "position": "Need to account for implementation and training costs in first year",
      "issues_raised": ["hidden_costs", "timeline_assumptions"], 
      "confidence": 0.75
    },
    {
      "round": 2, 
      "agent": "adversary",
      "position": "Sample bias in studies - mostly successful implementations reported",
      "issues_raised": ["selection_bias", "survivorship_bias"],
      "confidence": 0.68
    }
  ],
  "verdict": {
    "consensus_reached": true,
    "final_confidence": 0.78,
    "approved_claims": ["claim-cost-reduction-modified"],
    "modifications_required": [
      {
        "claim_id": "claim-cost-reduction", 
        "modification": "Specify net cost reduction after 18-24 months to account for implementation costs",
        "reason": "Implementation costs reduce initial savings"
      }
    ]
  }
}
```

## Step 5: Expert Council Evaluation

Get domain expert perspectives on the strategic decision:

```bash
curl -X POST http://127.0.0.1:8080/experts/evaluate \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-005" \
  -d '{
    "tenant_id": "tutorial-company",
    "decision_context": {
      "type": "technology_investment",
      "domain": "customer_experience", 
      "timeline": "12_months",
      "budget_range": "100k-500k"
    },
    "claims": [
      {
        "id": "claim-cost-reduction-modified",
        "text": "AI customer support reduces net operational costs by 25-35% after 18-24 months",
        "confidence": 0.78
      }
    ],
    "expert_disciplines": ["customer_experience", "technology_implementation", "financial_analysis"]
  }'
```

**Expert evaluation response:**
```json
{
  "evaluation_id": "eval-expert-council-001",
  "expert_memos": [
    {
      "discipline": "customer_experience",
      "expert_id": "cx-expert-001", 
      "assessment": {
        "recommendation": "proceed_with_caution",
        "confidence": 0.72,
        "key_risks": ["customer_adoption_curve", "escalation_complexity"],
        "success_factors": ["proper_training_data", "human_escalation_paths"]
      }
    },
    {
      "discipline": "technology_implementation",
      "expert_id": "tech-expert-001",
      "assessment": {
        "recommendation": "recommend",
        "confidence": 0.81, 
        "key_risks": ["integration_complexity", "data_quality"],
        "success_factors": ["phased_rollout", "robust_fallback_systems"]
      }
    },
    {
      "discipline": "financial_analysis", 
      "expert_id": "finance-expert-001",
      "assessment": {
        "recommendation": "recommend",
        "confidence": 0.76,
        "roi_timeline": "24_months",
        "break_even_month": 18
      }
    }
  ]
}
```

## Step 6: Generate Final Recommendations

Synthesize all analysis into actionable strategic recommendations:

```bash
curl -X POST http://127.0.0.1:8080/recommendations \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-006" \
  -d '{
    "tenant_id": "tutorial-company",
    "experiment_id": "exp-ai-support-001",
    "session_id": "session-comprehensive-001",
    "debate_id": "debate-ai-support-001", 
    "evaluation_id": "eval-expert-council-001",
    "decision_criteria": {
      "risk_tolerance": "medium",
      "timeline": "flexible",
      "budget_constraint": "moderate"
    }
  }'
```

**Final strategic recommendations:**
```json
{
  "decision_brief": {
    "id": "brief-ai-support-investment", 
    "title": "AI-Powered Customer Support Investment Strategy",
    "executive_summary": "Recommend proceeding with phased AI customer support implementation targeting 30% cost reduction over 24 months",
    "key_recommendations": [
      {
        "action": "Implement AI chatbot for Tier 1 support",
        "timeline": "Months 1-6", 
        "success_metric": "Handle 60% of initial inquiries",
        "investment": "$150k-200k"
      },
      {
        "action": "Develop comprehensive training dataset", 
        "timeline": "Months 2-4",
        "success_metric": "95%+ accuracy on common issues",
        "investment": "$50k-75k"
      },
      {
        "action": "Establish human escalation protocols",
        "timeline": "Month 3",
        "success_metric": "< 2min escalation time", 
        "investment": "$25k process redesign"
      }
    ],
    "risk_mitigation": [
      "Phased rollout to minimize disruption",
      "Robust fallback to human agents",
      "Continuous monitoring and optimization"
    ],
    "expected_outcomes": {
      "cost_reduction": "25-35% net savings by month 24",
      "customer_satisfaction": "10-15% improvement",
      "operational_efficiency": "40% faster initial response times"
    },
    "confidence_score": 0.78
  },
  "implementation_roadmap": {
    "phase_1": "Technology selection and procurement (Months 1-2)",
    "phase_2": "Integration and testing (Months 3-5)", 
    "phase_3": "Pilot deployment (Month 6)",
    "phase_4": "Full rollout and optimization (Months 7-12)"
  }
}
```

## Step 7: Quality Gate Evaluation

Finally, run evaluation gates to ensure the analysis meets quality standards:

```bash
curl -X POST http://127.0.0.1:8080/evals/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-007" \
  -d '{
    "tenant_id": "tutorial-company",
    "suite": "strategic_analysis",
    "artifacts": {
      "decision_brief": "brief-ai-support-investment",
      "research_session": "session-comprehensive-001", 
      "debate_id": "debate-ai-support-001"
    },
    "thresholds": {
      "evidence_coverage": 0.8,
      "claim_confidence": 0.75,
      "recommendation_actionability": 0.8
    }
  }'
```

**Quality evaluation results:**
```json
{
  "run_id": "eval-strategic-analysis-001",
  "tenant_id": "tutorial-company",
  "passed": true, 
  "overall_score": 0.82,
  "metrics": {
    "evidence_coverage": 0.85,
    "claim_confidence": 0.78, 
    "recommendation_actionability": 0.84,
    "constitutional_compliance": 0.89
  },
  "quality_gates": {
    "sufficient_evidence": "passed",
    "diverse_perspectives": "passed", 
    "actionable_recommendations": "passed",
    "risk_assessment": "passed"
  }
}
```

## Summary

Congratulations! You've completed a comprehensive strategic analysis using StratMaster's full capabilities:

### ✅ What You Accomplished

1. **Strategic Context**: Defined business scenario with clear success metrics
2. **Comprehensive Research**: Planned and executed multi-faceted research  
3. **Evidence Collection**: Gathered structured claims with source validation
4. **Multi-Agent Validation**: Used debate system to identify biases and strengthen findings
5. **Expert Evaluation**: Incorporated domain expertise across multiple disciplines
6. **Strategic Synthesis**: Generated actionable recommendations with implementation roadmap
7. **Quality Assurance**: Validated analysis quality through automated evaluation gates

### 🔑 Key Insights

- **Evidence-First Approach**: Every claim is backed by credible sources
- **Perspective Diversity**: Multi-agent and expert systems catch blind spots  
- **Implementation Focus**: Recommendations include timelines, metrics, and risk mitigation
- **Quality Standards**: Automated gates ensure consistent analysis quality

## Next Steps

| Goal | Next Tutorial |
|------|---------------|
| **Add multi-agent debate** | [Multi-Agent Debate Setup](multi-agent-setup.md) |
| **Deploy to production** | [Production Deployment](production-deployment.md) |
| **Understand architecture** | [Architecture Overview](../explanation/architecture.md) |
| **Customize configurations** | [Configuration Management](../how-to/configuration.md) |

## Further Reading

- [Multi-Agent Debate System](../explanation/multi-agent-debate.md) - Deep dive into AI validation
- [Constitutional AI Framework](../explanation/constitutional-ai.md) - Understanding safety guardrails  
- [API Reference](../reference/api/) - Complete endpoint documentation
- [Performance Tuning](../how-to/performance-tuning.md) - Optimize for larger analyses

---

<div class="success">
<p><strong>🎯 Achievement Unlocked!</strong> You've mastered StratMaster's complete strategic analysis workflow. You're ready to tackle real business challenges with AI-powered strategic intelligence!</p>
</div>
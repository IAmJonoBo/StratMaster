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

First, let's establish the business context with a strategic experiment:

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
  "experiment_id": "exp-ai-support-analysis",
  "tenant_id": "tutorial-company",
  "status": "created",
  "hypothesis_id": "hyp-ai-support-roi",
  "created_at": "2024-01-18T11:00:00Z"
}
```

## Step 2: Comprehensive Research Planning

Create a detailed research plan that covers multiple angles:

```bash
curl -X POST http://127.0.0.1:8080/research/plan \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-002" \
  -d '{
    "query": "AI customer support ROI B2B SaaS cost reduction satisfaction metrics",
    "tenant_id": "tutorial-company",
    "max_sources": 10,
    "research_depth": "comprehensive",
    "focus_areas": [
      "cost_analysis",
      "customer_satisfaction",
      "implementation_challenges",
      "competitive_advantage"
    ]
  }'
```

## Step 3: Execute Research with Evidence Collection

Run the comprehensive research plan:

```bash
curl -X POST http://127.0.0.1:8080/research/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-003" \
  -d '{
    "plan_id": "plan-comprehensive-ai-support",
    "tenant_id": "tutorial-company",
    "evidence_validation": true
  }'
```

**Expected response includes multiple claims with evidence:**
```json
{
  "session_id": "session-comprehensive-analysis",
  "claims": [
    {
      "id": "claim-cost-reduction",
      "text": "AI customer support systems typically reduce operational costs by 20-40%",
      "confidence": 0.78,
      "evidence_count": 5,
      "controversy_score": 0.2
    },
    {
      "id": "claim-satisfaction",
      "text": "Customer satisfaction with AI support varies by implementation quality",
      "confidence": 0.65,
      "evidence_count": 7,
      "controversy_score": 0.6
    }
  ],
  "evidence_summary": {
    "total_sources": 8,
    "peer_reviewed": 3,
    "industry_reports": 4,
    "case_studies": 1
  }
}
```

## Step 4: Multi-Agent Debate for Validation

Now comes the powerful part - let's validate our findings through multi-agent debate:

```bash
curl -X POST http://127.0.0.1:8080/debate/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-004" \
  -d '{
    "tenant_id": "tutorial-company",
    "hypothesis_id": "hyp-ai-support-roi",
    "claim_ids": ["claim-cost-reduction", "claim-satisfaction"],
    "max_turns": 3,
    "agent_config": {
      "proponent": "optimistic_analyst",
      "critic": "conservative_analyst",
      "moderator": "experienced_strategist"
    }
  }'
```

**The debate response shows agent interactions:**
```json
{
  "debate_id": "debate-ai-support-validation",
  "status": "completed",
  "turns": 3,
  "final_consensus": {
    "claim_cost_reduction": {
      "validated": true,
      "confidence_adjustment": -0.1,
      "key_concerns": ["implementation_complexity", "training_costs"]
    },
    "claim_satisfaction": {
      "validated": false,
      "confidence_adjustment": -0.3,
      "key_concerns": ["customer_preference_variation", "support_complexity"]
    }
  }
}
```

## Step 5: Generate Strategic Recommendations

With validated claims, generate actionable recommendations:

```bash
curl -X POST http://127.0.0.1:8080/recommendations \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-005" \
  -d '{
    "tenant_id": "tutorial-company",
    "cep_id": "cep-b2b-saas-support",
    "jtbd_ids": ["jtbd-reduce-support-costs", "jtbd-improve-satisfaction"],
    "risk_tolerance": "medium",
    "time_horizon": "12_months",
    "context": {
      "debate_id": "debate-ai-support-validation",
      "validated_claims": ["claim-cost-reduction"]
    }
  }'
```

**Strategic recommendations response:**
```json
{
  "decision_brief": {
    "id": "brief-ai-support-decision",
    "title": "AI Customer Support Investment Decision",
    "executive_summary": "Implement AI customer support in phased approach with strong human oversight",
    "key_recommendations": [
      {
        "title": "Phase 1: Pilot Implementation",
        "description": "Deploy AI for tier-1 support questions with 6-month evaluation",
        "priority": "high",
        "confidence": 0.75,
        "investment_required": "$50K-$100K"
      },
      {
        "title": "Enhanced Training Program",
        "description": "Invest in comprehensive AI training and customer communication",
        "priority": "high", 
        "confidence": 0.82,
        "investment_required": "$25K-$50K"
      }
    ],
    "risk_assessment": {
      "implementation_risk": "medium",
      "financial_risk": "low",
      "customer_satisfaction_risk": "medium-high"
    }
  }
}
```

## Step 6: Evaluation and Quality Gates

Finally, run quality evaluation on our analysis:

```bash
curl -X POST http://127.0.0.1:8080/evals/run \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: analysis-tutorial-006" \
  -d '{
    "tenant_id": "tutorial-company",
    "suite": "strategic_analysis",
    "target": {
      "type": "decision_brief",
      "id": "brief-ai-support-decision"
    },
    "thresholds": {
      "evidence_quality": 0.7,
      "reasoning_coherence": 0.75,
      "actionability": 0.8
    }
  }'
```

## Step 7: Review Your Complete Analysis

You've now completed a full strategic analysis workflow! Let's review what you accomplished:

### Analysis Components Created

1. **Strategic Experiment** - Defined hypothesis and success metrics
2. **Research Plan** - Comprehensive multi-angle investigation  
3. **Evidence Collection** - Gathered and validated supporting data
4. **Multi-Agent Debate** - Cross-examined claims for reliability
5. **Strategic Recommendations** - Generated actionable next steps
6. **Quality Evaluation** - Assessed analysis rigor and completeness

### Key Learning Points

- **Evidence-Grounded**: All recommendations backed by validated research
- **Multi-Perspective**: Debate process catches blind spots and biases
- **Risk-Aware**: Explicit assessment of implementation challenges
- **Actionable**: Clear next steps with priorities and investment levels
- **Measurable**: Success metrics defined upfront for tracking

## Next Steps

### Explore Advanced Features

- **Custom Agent Configuration**: Train specialized debate agents
- **Industry-Specific Research**: Use domain-focused research templates
- **Integration Workflows**: Connect with existing business systems
- **Monitoring Dashboards**: Track recommendation implementation

### Deployment Options

- **Local Development**: Continue with current setup for experimentation
- **Team Deployment**: Set up shared infrastructure for collaboration
- **Enterprise Integration**: Connect to existing strategy processes

### Additional Tutorials

| Topic | Description |
|-------|-------------|
| [Multi-Agent Setup](multi-agent-setup.md) | Configure specialized debate agents |
| [Production Deployment](production-deployment.md) | Deploy for team/enterprise use |

## Troubleshooting

### Common Issues

**Long processing times:**
- Complex analyses may take 5-10 minutes
- Monitor progress via status endpoints
- Consider reducing research scope for testing

**Debate consensus failures:**
- Lower consensus thresholds in agent config
- Review claim evidence quality
- Try different agent personality configurations

**Low confidence scores:**
- Increase research depth and source count
- Focus on peer-reviewed and authoritative sources
- Consider domain expertise validation

### Getting Help

- **How-to Guides**: [Troubleshooting](../how-to/troubleshooting.md) for specific issues
- **Reference Docs**: [API Reference](../reference/api/) for endpoint details
- **Community**: [GitHub Discussions](https://github.com/IAmJonoBo/StratMaster/discussions)

---

!!! success "Analysis Complete!"
    
    You've successfully built a complete strategic analysis using StratMaster's multi-agent system. The approach demonstrates how AI can augment human strategic thinking with evidence-based validation and collaborative reasoning.

!!! tip "Next Challenge"
    
    Try applying this workflow to a strategic question from your own organization. Start with a clear hypothesis and success metrics, then let the system guide you through evidence-based decision making.
# Expert Council Delphi Process Instructions

## Overview

The Expert Council uses a two-round Delphi method to achieve convergence on strategy assessments. This process ensures that expert opinions are systematically collected, shared, and refined to reach a stable consensus.

## Round 1: Independent Assessment

Each expert provides their initial assessment based on their discipline's doctrine:

1. **Individual Review**: Each expert reviews the strategy independently using their discipline's specific rubric/checklist
2. **Initial Scoring**: Provide numerical scores (0.0-1.0) for relevant assessment criteria
3. **Justification**: Document reasoning and cite specific doctrine rules that inform the assessment
4. **Findings**: Identify specific issues, risks, or recommendations within their domain expertise

**Output Format**: Each expert submits a `DisciplineMemo` with findings, scores, and recommendations.

## Round 2: Informed Consensus

After Round 1 results are aggregated and anonymously shared:

1. **Review Others**: Each expert reviews the anonymous aggregate findings from other disciplines
2. **Reconsider**: Experts may revise their initial assessment considering interdisciplinary insights
3. **Stability Check**: If any expert's score changes by >10% (configurable threshold), flag for review
4. **Final Vote**: Submit final `DisciplineVote` with updated score and justification

**Output Format**: Each expert submits a final `DisciplineVote` that may incorporate insights from other disciplines.

## Convergence Criteria

- **Stability**: No expert changes their score by more than the configured threshold (default: 0.10)
- **Completion**: All experts submit both rounds within the specified timeframe
- **Quality**: All votes include substantive justification referencing relevant doctrine rules

## Weighting and Aggregation

Final council score is computed as a weighted average using discipline weights from `configs/experts/weights.yaml`:

```
council_score = Σ(discipline_weight_i × discipline_score_i)
```

## Output

The process produces a `CouncilVote` containing:
- Individual discipline votes and justifications
- Weighted aggregate score
- Applied weights for transparency
- Stability indicators and convergence metrics

## Quality Assurance

- All assessments must reference specific doctrine rules
- Scores below council minimum threshold trigger automatic review
- High reactance risk (>0.40) generates warnings; >0.50 blocks deployment
- WCAG AA violations are treated as blocking issues for accessibility compliance
# Expert Council Implementation

This directory contains the Expert Council models, configurations, and supporting documentation for the StratMaster AI-powered brand strategy platform.

## Overview

The Expert Council provides multi-disciplinary assessment of brand strategies using structured evaluation frameworks from psychology, design, communication, accessibility, and behavioral economics. The system implements a Delphi-style consensus process with weighted expert opinions and configurable evaluation thresholds.

## Architecture

### Models (`packages/api/src/stratmaster_api/models/experts/`)

- **`ExpertProfile`**: Profile definition for domain experts with discipline, capabilities, and calibration data
- **`Doctrine`**: Rubrics and checklists defining evaluation criteria for each discipline
- **`DisciplineMemo`**: Assessment output from individual experts including findings and recommendations  
- **`CouncilVote`**: Weighted consensus vote from the entire expert council
- **`MessageMap`**: Structured communication template (audience→problem→value→proof→CTA)
- **`PersuasionRisk`**: Psychological reactance assessment for messaging

### Configuration (`configs/experts/`)

- **`weights.yaml`**: Default weights for each discipline and update parameters
- **`doctrines/`**: Discipline-specific evaluation frameworks:
  - `design/heuristics.nng.yaml`: Nielsen Norman Group 10 usability heuristics
  - `accessibility/wcag21-aa-min.yaml`: WCAG 2.1 Level AA requirements
  - `psychology/com-b.yaml`: COM-B behavior change model  
  - `psychology/east.yaml`: EAST behavioral insights framework
  - `communication/message-map.yaml`: Strategic message structure requirements
  - `psychology/reactance-phrases.txt`: Psychological reactance trigger phrases

### Evaluation Gates (`configs/evals/thresholds.yaml`)

New expert-specific thresholds added:
- `usability_score_min: 0.75`: Minimum composite design+communication score
- `wcag_aa_required: true`: Accessibility compliance requirement
- `reactance_risk_warn: 0.40` / `reactance_risk_block: 0.50`: Reactance thresholds
- `message_map_min: 0.85`: Message completeness requirement
- `council_score_min: 0.75`: Overall council approval threshold
- `council_stability_delta_warn: 0.10`: Delphi convergence stability

### Prompts (`prompts/experts/`)

- **`delphi-instructions.md`**: Two-round Delphi consensus process documentation
- **`council-style.md`**: Expert communication style guide with doctrine citation requirements

## Usage

### Schema Generation

Generate JSON schemas for all Expert Council models:

```bash
python packages/api/src/stratmaster_api/models/experts/generate_json_schemas.py
```

### Testing

Run Expert Council model tests:

```bash
pytest tests/unit/models/experts/ -v
```

### Integration with Orchestrator

Expert Council models integrate with the existing orchestrator system through:

1. **Constitutional Integration**: Expert doctrines complement existing constitutional prompts in `prompts/constitutions/`
2. **Evaluation Gates**: Expert thresholds integrate with existing evaluation system in `configs/evals/thresholds.yaml`
3. **Agent Debate**: Expert assessments feed into the existing debate system via `DebateTrace` and `DebateTurn` models

## Validation

All configuration files have been validated:
- ✓ Python syntax validation for all model files
- ✓ YAML syntax validation for all configuration files
- ✓ Pydantic model validation with strict mode and extra field restrictions
- ✓ JSON schema generation capability confirmed

## References

The Expert Council implementation references established frameworks:

- **Nielsen Norman Group**: 10 Usability Heuristics for User Interface Design
- **W3C WCAG 2.1**: Web Content Accessibility Guidelines Level AA
- **COM-B Model**: Susan Michie's Behaviour Change Wheel framework  
- **EAST Framework**: UK Behavioural Insights Team behavioral framework
- **Psychological Reactance Theory**: Brehm (1966) and Self-Determination Theory

## Next Steps

1. **Service Integration**: Wire Expert Council into MCP servers and API endpoints
2. **Agent Implementation**: Create expert agent nodes for LangGraph orchestration
3. **Evaluation Harness**: Integrate with existing evaluation pipelines
4. **Dashboard Integration**: Surface expert assessments in monitoring and reporting
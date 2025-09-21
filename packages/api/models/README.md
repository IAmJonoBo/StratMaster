# API Model Suite

Defines Pydantic v2 models for StratMaster API responses and contract schemas.

## Models

Implemented under `packages/api/src/stratmaster_api/models/`:

- `Source` — identifies provenance (`type`, `reference`, `url`, `collected_at`).
- `Provenance` — wraps source metadata with fingerprint and SAST timestamp.
- `Claim` — statement produced by agents, includes supporting evidence IDs and
  confidence scores.
- `Assumption` — hypotheses feeding experiments, includes owner, expiry date.
- `Hypothesis` — structured research hypothesis with metrics and decision log.
- `Experiment` — describes planned or executed experiments with metrics + outcome.
- `Metric` — name, definition, unit, baseline, target.
- `Forecast` — scenario projections with intervals and underlying assumptions.
- `CEP` — customer engagement play blueprint (links to JTBD, metrics).
- `JTBD` — job-to-be-done statements with context, persona, desired outcome.
- `DBA` — data-backed artefact summarising dashboards or datasets.

Each model exports validation hooks ensuring:

- Fingerprints are SHA-256 strings prefixed with `sha256:`.
- Timestamps are timezone-aware and normalised to UTC.
- Cross-entity references (e.g. `Claim.supporting_evidence`) exist in payloads.

## JSON Schema generation

- Run `python -m stratmaster_api.models.export --output dist/schemas` to generate
  versioned `$id` JSON Schemas (e.g. `https://schemas.stratmaster.ai/v1/claim.json`).
- Schemas published via API endpoint `GET /schemas/{model}`.
- CI validates schemas against sample payloads in `packages/api/tests/fixtures`.

## Usage

```python
from stratmaster_api.models import Claim

payload = Claim.model_validate(sample_data)
print(payload.supporting_evidence)
```

## Testing

- Run `pytest packages/api/tests/test_models.py` to execute validation tests.
- Contract tests load JSON examples from `tests/fixtures/models/` and assert round-trip.

## Extensibility

- Add new models by creating a Pydantic class and exporting schema via the helper.
- Update `docs/api/models.md` with field definitions and provide example payloads.
- Bump schema version when introducing breaking changes.

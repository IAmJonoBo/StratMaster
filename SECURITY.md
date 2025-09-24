# Security Policy

## Reporting a vulnerability

If you discover a security issue, please do not open a public issue. Instead, email the maintainers or open a private security advisory in GitHub (Security > Advisories).

Provide as much detail as possible, including reproduction steps and potential impact.

## Supported versions

This project is under active development; the `main` branch is supported.

## Frontier audit security actions

- **Threat modelling** – contributions must update the STRIDE catalogue under `ops/threat-model/` when introducing new services or data flows so mitigation status stays accurate.【F:ops/threat-model/stride.md†L1-L3】
- **SBOM & supply chain** – container and package changes must produce CycloneDX SBOM artifacts in CI and attach provenance metadata as described in the implementation plan.【F:.github/workflows/ci.yml†L55-L145】【F:IMPLEMENTATION_PLAN.md†L25-L67】
- **Vulnerability management** – coordinate with maintainers to triage pip-audit/bandit findings surfaced in CI; do not ignore failing security jobs.
- **Secrets & telemetry** – ensure any new telemetry exporters follow least-privilege principles and redact PII before emitting metrics, aligning with the operations guide.【F:docs/operations-guide.md†L135-L171】

# compression-mcp — Stub

Scope: Expose LLMLingua-based prompt compression as an MCP tool to reduce token costs while preserving essential meaning.

Planned tools:

- compress.prompt(text, target_tokens, mode)

Notes:

- Apply only to narrative prompts; never compress provenance or numeric results.
- Log compression efficiency and quality deltas (Ragas/FActScore) as per blueprint.
- Enforce per-tenant policies/limits before invoking.

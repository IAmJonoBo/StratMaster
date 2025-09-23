# Open Questions

The following clarifications are required to proceed with high-confidence implementation of the frontier roadmap:

1. **Seed Corpus Definition**
   - What canonical documents (formats, size, licence) should be included in the demo/offline seed bundle? Existing seeds/fixtures cover limited scope.
2. **Model Allow-List**
   - Which OSS foundation models are approved for production (Mixtral, Llama 3, Nous-Hermes, Phi-3, etc.) and what licence constraints must be enforced per tenant?
3. **Usage Analytics Requirements**
   - Do stakeholders require anonymised usage analytics dashboards beyond existing Grafana metrics (e.g., retention, engagement) and if so what privacy thresholds apply?
4. **Expert Council Composition**
   - Confirm the list of disciplines and weighting schemes for the Expert Council MCP to avoid rework during PR-F.
5. **CI Budget**
   - What is the acceptable upper bound for CI runtime per push (minutes) to balance added eval/security jobs vs. developer productivity?

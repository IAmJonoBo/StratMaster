# K8s Network Policies — Stub

- Define strict egress/ingress per service and tenant; deny-by-default.
- TODO[INF-416a]: Provide concrete NetworkPolicy manifests per component and tie them to `ops/policies/*.rego` controls (`docs/backlog.md#todo-inf-416-network-policies`).
- TODO[INF-416b]: Document multi-tenant isolation strategy and test approach (kubectl traces, conformance suites).

# Error Handling & Incident Loop

```mermaid
flowchart LR
    API[Gateway API]
    MCP[MCP Services]
    Queue[Retry Queue]
    Alerts[Alerting]
    Oncall[On-call Responder]
    Postmortem[Postmortem Workflow]
    Dashboard[Grafana/Langfuse]

    API -->|Non-2xx| Queue
    MCP -->|Exception| Queue
    Queue -->|Retry policy| MCP
    Queue -->|Exhausted| Alerts

    Alerts --> Oncall
    Oncall --> Dashboard
    Dashboard --> Oncall
    Oncall -->|Mitigate| API
    Oncall -->|Mitigate| MCP
    Oncall --> Postmortem
    Postmortem -->|Action items| API
    Postmortem -->|Action items| MCP
```

**Notes**
- Retries follow service-specific backoff policies before escalating to alerts.
- Alerts should be wired into PagerDuty/Slack once SLO breaches are defined.
- Postmortem action items feed backlog grooming for reliability improvements.

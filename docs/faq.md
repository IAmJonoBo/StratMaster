---
title: Frequently Asked Questions
description: Common questions and answers about StratMaster
version: 0.1.0
nav_order: 11
parent: Documentation
---

# Frequently Asked Questions

## Getting Started

### What is StratMaster?
StratMaster is an AI-powered Brand Strategy platform that combines evidence-grounded research, multi-agent debate, and constitutional AI to deliver reliable strategic recommendations. It's designed for businesses, consultants, and analysts who need high-quality strategic intelligence backed by credible evidence.

### Who should use StratMaster?
- **Business Strategists** planning market entry, product launches, or competitive positioning
- **Management Consultants** conducting client analysis and recommendations
- **Market Researchers** seeking comprehensive competitive intelligence
- **Product Managers** evaluating feature priorities and market opportunities
- **Investment Analysts** performing due diligence and market assessment

### What makes StratMaster different from ChatGPT or other AI tools?
| Feature | StratMaster | General AI Tools |
|---------|-------------|------------------|
| **Evidence Grounding** | Every claim requires credible sources | Often unsourced or hallucinated |
| **Multi-Agent Validation** | Claims validated by adversarial debate | Single model responses |
| **Strategic Focus** | Purpose-built for business strategy | General-purpose chat |
| **Quality Gates** | Automated accuracy and bias checking | No systematic validation |
| **Audit Trail** | Complete provenance and reasoning | Limited explainability |
| **Constitutional AI** | Built-in safety and accuracy guardrails | Minimal safety constraints |

### How quickly can I get started?
You can be running StratMaster locally in under 10 minutes:

1. **Clone the repository**: `git clone https://github.com/IAmJonoBo/StratMaster.git`
2. **Bootstrap environment**: `make bootstrap` (~2-3 minutes)  
3. **Start API server**: `make api.run` (~30 seconds)
4. **Make your first request**: Follow the [Quick Start Tutorial](tutorials/quickstart.md)

## Technical Questions

### What are the system requirements?
**Minimum**:
- Python 3.11+
- 4GB RAM
- 10GB free storage
- Docker Desktop (optional but recommended)

**Recommended**:
- Python 3.12+
- 8GB+ RAM  
- 20GB+ free storage
- Docker Desktop latest version

### Which platforms are supported?
- ✅ **Linux**: Ubuntu 20.04+, CentOS 8+, Debian 11+
- ✅ **macOS**: 10.15+ (Intel and Apple Silicon)
- ✅ **Windows**: Windows 10+ with WSL2

### Do I need GPU resources?
**No**, StratMaster works entirely on CPU. It's designed to use local AI models (like Ollama) or cloud APIs, so GPU acceleration is optional and not required for any core functionality.

### Can I run this in production?
**Yes**, StratMaster is production-ready with:
- Docker and Kubernetes deployment support
- Comprehensive monitoring and observability
- Multi-tenant architecture with data isolation
- Enterprise authentication (Keycloak, SAML, OIDC)
- Automated scaling and load balancing

### What databases does it use?
StratMaster uses a multi-modal data architecture:
- **PostgreSQL**: Transactional data, user accounts, audit logs
- **Qdrant**: Vector embeddings for semantic search
- **OpenSearch**: Full-text search and log aggregation  
- **NebulaGraph**: Knowledge graphs and relationship modeling
- **MinIO**: Object storage for documents and artifacts
- **Redis**: Caching, sessions, and rate limiting

## AI and Data Questions

### Does StratMaster send my data to OpenAI or other external services?
**By default, no**. StratMaster is designed with privacy-first principles:
- External AI providers (OpenAI, Anthropic) are **disabled by default**
- The system uses local AI models via Ollama by default
- You control all data and AI routing decisions
- When external providers are enabled, you can configure privacy settings to limit data sharing

### How accurate are the AI-generated recommendations?
StratMaster uses multiple validation mechanisms to ensure accuracy:
- **Multi-Agent Debate**: Claims are challenged by adversarial agents
- **Evidence Requirements**: Every claim must cite credible sources
- **Constitutional AI**: Built-in accuracy and safety guardrails
- **Quality Gates**: Automated evaluation using FactScore, TruthfulQA, and other metrics
- **Expert Validation**: Domain expert simulation for specialized knowledge

Typical accuracy metrics:
- **Fact Accuracy**: 85-90% (validated against ground truth)
- **Source Citation**: 95%+ (all claims have supporting evidence)
- **Constitutional Compliance**: 90%+ (safety and accuracy guardrails)

### Can I customize the AI models used?
**Yes**, StratMaster supports multiple AI providers:
- **Local Models**: Ollama, vLLM, or custom deployments
- **Cloud APIs**: OpenAI, Anthropic, Google, Azure (optional)
- **Custom Models**: Fine-tuned models for specific domains
- **Hybrid Routing**: Intelligent routing based on task requirements and privacy settings

### How does the multi-agent debate system work?
The system uses four specialized agents:
1. **Strategist**: Proposes claims and recommendations
2. **Critic**: Challenges methodology and evidence quality
3. **Adversary**: Tests worst-case scenarios and edge cases
4. **Moderator**: Facilitates consensus and final synthesis

Each agent has different perspectives and goals, creating robust validation through adversarial testing. See [Multi-Agent Debate System](explanation/multi-agent-debate.md) for details.

## Features and Capabilities

### What types of strategic analysis can StratMaster perform?
- **Market Analysis**: Competitive landscape, market size, trends
- **Product Strategy**: Feature prioritization, positioning, launch planning
- **Business Model Analysis**: Revenue streams, cost structures, scalability
- **Risk Assessment**: Market risks, competitive threats, implementation challenges
- **Investment Analysis**: ROI projections, cost-benefit analysis, scenario planning
- **Compliance Analysis**: Regulatory requirements, policy implications

### Can I upload my own documents for analysis?
**Yes**, StratMaster includes document ingestion capabilities:
- **Supported Formats**: PDF, Word, PowerPoint, Excel, plain text
- **Content Processing**: Automatic extraction, chunking, and analysis
- **Quality Assessment**: Confidence scoring and clarification prompts
- **Knowledge Integration**: Documents become part of your knowledge base
- **Privacy**: All documents stay within your deployment

### How does StratMaster handle different industries?
The system includes domain expertise through:
- **Expert Council**: Simulated domain experts across disciplines
- **Industry Knowledge**: Configurable knowledge bases for specific sectors
- **Custom Prompts**: Industry-specific analysis frameworks
- **Regulatory Awareness**: Built-in compliance and regulatory knowledge

### Can multiple people collaborate on an analysis?
**Yes**, Phase 2 includes collaboration features:
- **Real-time Collaboration**: WebSocket-based shared workspaces
- **Role-based Access**: Different permissions for analysts, reviewers, stakeholders
- **Approval Workflows**: Multi-stage review and approval processes
- **Audit Trails**: Complete history of changes and decisions
- **Mobile Support**: Mobile app for approvals and reviews

## Deployment and Operations

### How do I deploy StratMaster in my organization?
Several deployment options are available:

**Local Development**:
```bash
make bootstrap && make dev.up
```

**Production Docker**:
```bash
docker compose -f docker-compose.prod.yml up -d
```

**Kubernetes**:
```bash
helm install stratmaster ./helm/stratmaster-api
```

### What monitoring and observability features are included?
Comprehensive observability stack:
- **Metrics**: Prometheus for system and business metrics
- **Dashboards**: Grafana with pre-built dashboards
- **Tracing**: OpenTelemetry distributed tracing
- **Logging**: Structured logging with correlation IDs
- **LLM Observability**: Langfuse for AI model monitoring
- **Alerts**: Configurable alerting for operational issues

### How do I backup and restore data?
Built-in backup strategies:
- **Database Backups**: Automated PostgreSQL dumps
- **Vector Data**: Qdrant collection exports
- **Object Storage**: MinIO bucket replication
- **Configuration**: GitOps-based configuration management
- **Disaster Recovery**: Multi-region deployment support

### What about compliance and security?
Enterprise-grade security:
- **Data Encryption**: TLS in transit, AES-256 at rest
- **Authentication**: Multi-factor, SSO, RBAC
- **Audit Logging**: Complete audit trail of all operations
- **Network Security**: VPN, network segmentation, firewall rules
- **Compliance**: GDPR, SOC2, HIPAA-ready architecture
- **Vulnerability Management**: Automated dependency scanning

## Cost and Licensing

### Is StratMaster open source?
**Yes**, StratMaster is open source under the MIT License. You can:
- Use it freely for commercial and personal projects
- Modify and distribute it
- Build proprietary applications on top
- Contribute back to the community

### What are the operational costs?
Costs depend on your deployment model:

**Self-Hosted (Minimal)**:
- Server/cloud costs only
- No per-user or per-request fees
- Local AI models (free)

**Cloud Services (Optional)**:
- External AI APIs (if enabled): $10-100/month depending on usage
- Managed databases: $50-500/month depending on scale
- Monitoring services: $20-200/month

**Enterprise Support (Future)**:
- Professional services and support available
- Custom implementations and integrations
- SLA guarantees and priority support

### Can I use this commercially?
**Yes**, the MIT License allows unrestricted commercial use. You can:
- Deploy in your organization
- Build commercial products on top
- Offer it as a service to clients
- Integrate with proprietary systems

## Troubleshooting

### The bootstrap command fails with network timeouts
This is common in corporate environments with restrictive firewalls:

**Solutions**:
1. **Use Docker**: `make test-docker` (bypasses local Python issues)
2. **Configure proxy**: Set `HTTP_PROXY` and `HTTPS_PROXY` environment variables
3. **Use lock files**: Install from `requirements.lock` for reproducible builds
4. **Corporate network**: Contact IT to whitelist Python package repositories

### Tests are failing
Check the current status:
```bash
# Run quick API tests
PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q

# Expected: 23 passed in ~1.6s
```

If tests fail:
1. **Check Python version**: Must be 3.11+
2. **Clean environment**: `make clean && make bootstrap`
3. **Check dependencies**: Ensure all required packages installed
4. **Review logs**: Look for specific error messages

### Docker containers won't start
Common Docker issues:

**Port conflicts**:
```bash
# Find process using port 8080
lsof -ti:8080
# Kill if necessary
lsof -ti:8080 | xargs kill -9
```

**Out of disk space**:
```bash
# Clean Docker system
docker system prune -a
```

**Memory issues**:
```bash
# Check Docker resource limits
docker system info | grep -i memory
```

### API returns 500 errors
Debug API issues:

1. **Check logs**: `docker compose logs api`
2. **Verify dependencies**: Ensure all databases are running
3. **Test connectivity**: `curl http://localhost:8080/healthz`
4. **Enable debug mode**: `STRATMASTER_LOG_LEVEL=DEBUG`

### Performance is slow
Performance optimization:

1. **Check resource usage**: `docker stats`
2. **Tune database connections**: Increase pool sizes
3. **Enable caching**: Configure Redis appropriately  
4. **Scale services**: Increase replica counts
5. **Monitor metrics**: Use Grafana dashboards to identify bottlenecks

## Getting Help

### Where can I find more documentation?
- **Tutorials**: Step-by-step learning guides
- **How-to Guides**: Problem-solving recipes
- **Reference**: Complete API and CLI documentation
- **Explanation**: Deep dives into architecture and concepts

### How do I report bugs or request features?
- **GitHub Issues**: For bugs, feature requests, and technical questions
- **GitHub Discussions**: For general questions and community discussions
- **Security Issues**: Use the responsible disclosure process in SECURITY.md

### Is there a community?
The StratMaster community is growing:
- **GitHub Discussions**: Active community Q&A
- **Contributor Program**: Welcome contributions of all types
- **Documentation**: Community-maintained guides and examples
- **Regular Updates**: Frequent releases with new features

### Can I get professional support?
While the open source project is community-supported, professional services may be available for:
- **Custom implementations**
- **Enterprise integrations**
- **Performance optimization**
- **Training and onboarding**

Contact through GitHub Discussions for inquiries.

---

<div class="note">
<p><strong>💡 Didn't find your answer?</strong> Check the <a href="https://github.com/IAmJonoBo/StratMaster/discussions">GitHub Discussions</a> or <a href="https://github.com/IAmJonoBo/StratMaster/issues">open an issue</a>. The community is helpful and responsive!</p>
</div>
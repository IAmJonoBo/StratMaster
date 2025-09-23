---
title: StratMaster Documentation
description: Comprehensive documentation for the AI-powered Brand Strategy platform
version: 0.1.0
platform: Python 3.11+, Docker, Kubernetes
last_updated: 2024-01-18
nav_order: 1
has_children: true
---

# StratMaster Documentation

Welcome to the comprehensive documentation for **StratMaster**, an AI-powered Brand Strategy platform that combines evidence-grounded research, multi-agent debate, and constitutional AI to deliver reliable strategic recommendations.

## Quick Navigation

<div class="grid grid-3col">

### 🎯 [Tutorials](tutorials/)
Step-by-step guides to get you productive quickly:
- [Quick Start Tutorial](tutorials/quickstart.md) - Get up and running in 10 minutes
- [Your First Strategy Analysis](tutorials/first-analysis.md) - Build your first analysis
- [Production Deployment](tutorials/production-deployment.md) - Deploy to production

### 🔧 [How-to Guides](how-to/)
Problem-oriented recipes for common tasks:
- [Development Setup](how-to/development-setup.md) - Set up your dev environment
- [Configuration Management](how-to/configuration.md) - Manage configs effectively
- [Troubleshooting](how-to/troubleshooting.md) - Solve common problems

### 📚 [Reference](reference/)
Complete technical reference for APIs and CLIs:
- [API Reference](reference/api/) - All endpoints with examples
- [CLI Reference](reference/cli/) - Command-line tools
- [Configuration Reference](reference/configuration/) - All settings

### 💡 [Explanation](explanation/)
In-depth understanding of system design and concepts:
- [Architecture Overview](explanation/architecture.md) - System design
- [Multi-Agent Debate](explanation/multi-agent-debate.md) - Core AI approach
- [Security Model](explanation/security-model.md) - Security architecture

</div>

## What is StratMaster?

StratMaster is a production-ready AI platform that delivers strategic insights through:

- **🔍 Evidence-Grounded Research**: Web crawling with provenance tracking and PII hygiene
- **🧠 Knowledge Fabric**: GraphRAG + hybrid retrieval (Qdrant + OpenSearch + NebulaGraph)
- **🤖 Multi-Agent Debate**: Constitutional AI with critic and adversary validation
- **📊 Strategic Modeling**: CEPs, JTBD, DBAs, Experiments, and Forecasts as first-class objects
- **🔌 MCP Architecture**: Model Context Protocol for all tool/resource access
- **☁️ Cloud Native**: Kubernetes-ready with Helm charts and auto-scaling

## Getting Started

Choose your path based on your needs:

| I want to... | Start here |
|--------------|------------|
| **Try StratMaster quickly** | [Quick Start Tutorial](tutorials/quickstart.md) |
| **Understand the system** | [Architecture Overview](explanation/architecture.md) |
| **Set up for development** | [Development Setup](how-to/development-setup.md) |
| **Deploy to production** | [Production Deployment](tutorials/production-deployment.md) |
| **Find a specific API** | [API Reference](reference/api/) |
| **Solve a problem** | [Troubleshooting Guide](how-to/troubleshooting.md) |

## System Requirements

| Component | Requirement |
|-----------|-------------|
| **Python** | 3.11+ |
| **Docker** | Desktop 4.0+ (for full stack) |
| **Memory** | 4GB+ (8GB+ recommended) |
| **Storage** | 10GB+ free space |
| **Platform** | Linux, macOS, Windows (WSL2) |

## Version Information

- **Current Version**: 0.1.0
- **API Version**: v1
- **Python Support**: 3.11+
- **Docker Support**: ✅
- **Kubernetes Support**: ✅ (Helm 3.x)

## Community and Support

- **Documentation**: You're reading it! 📖
- **Issues**: [GitHub Issues](https://github.com/IAmJonoBo/StratMaster/issues)
- **Discussions**: [GitHub Discussions](https://github.com/IAmJonoBo/StratMaster/discussions)
- **Security**: [Security Policy](../SECURITY.md)

---

<div class="note">
<p><strong>💡 Tip:</strong> This documentation follows the <a href="https://diataxis.fr/">Diátaxis framework</a>. Each section serves a specific purpose:</p>
<ul>
<li><strong>Tutorials</strong> - Learning-oriented lessons</li>
<li><strong>How-to guides</strong> - Problem-oriented solutions</li>
<li><strong>Reference</strong> - Information-oriented technical specs</li>
<li><strong>Explanation</strong> - Understanding-oriented discussion</li>
</ul>
</div>
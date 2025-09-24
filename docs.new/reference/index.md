# Reference

Complete technical reference documentation for all StratMaster APIs, command-line tools, and configuration options. Use this section to look up specific implementation details, parameter lists, and technical specifications.

## API Reference

Complete documentation for all StratMaster APIs:

- **[API Overview](api/index.md)** - Introduction to the StratMaster API ecosystem
- **[Gateway API](api/gateway.md)** - Main FastAPI application endpoints
- **[Research MCP](api/research-mcp.md)** - Research orchestration service
- **[Knowledge MCP](api/knowledge-mcp.md)** - Knowledge graph and retrieval service  
- **[Router MCP](api/router-mcp.md)** - Request routing and load balancing
- **[OpenAPI Specification](api/openapi.md)** - Interactive API documentation

## CLI Reference

Command-line tools and build system:

- **[Make Commands](cli/make-commands.md)** - All available make targets
- **[Scripts](cli/scripts.md)** - Utility scripts and tools

## Configuration Reference

Complete configuration documentation:

- **[Environment Variables](configuration/environment.md)** - All environment configuration
- **[YAML Configuration](configuration/yaml-configs.md)** - Service configuration files

## Organization

This reference is organized by interface type:

### APIs
- RESTful HTTP APIs with request/response schemas
- OpenAPI specifications with interactive documentation
- Authentication and authorization details
- Rate limiting and error handling

### Command Line
- Make targets for build, test, and deployment
- Utility scripts for common tasks
- Environment setup and validation tools

### Configuration
- Environment variables for all services
- YAML configuration files and schemas
- Production deployment configurations
- Security and performance settings

!!! tip "Quick Lookup"
    
    Use the search functionality to quickly find specific endpoints, parameters, or configuration options.

## API Status

All APIs are versioned and stable unless marked otherwise:

- ✅ **Stable** - Production ready, follows semantic versioning
- ⚠️ **Beta** - Feature complete but may have breaking changes
- 🧪 **Alpha** - Under active development, expect changes
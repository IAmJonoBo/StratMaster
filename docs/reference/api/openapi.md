# OpenAPI Specification

The complete OpenAPI 3.1 specification for the StratMaster API. This interactive documentation allows you to explore all endpoints, request/response schemas, and test API calls directly from your browser.

## Interactive Documentation

<div class="grid cards" markdown>

-   :material-api:{ .lg .middle } **Swagger UI**

    ---

    Interactive API testing interface with request builders

    [:octicons-link-external-24: Open Swagger UI](http://localhost:8080/docs)

-   :material-book-open:{ .lg .middle } **ReDoc**

    ---

    Clean, printable API reference documentation

    [:octicons-link-external-24: Open ReDoc](http://localhost:8080/redoc)

</div>

## OpenAPI Specification

The complete OpenAPI specification is available in multiple formats:

- **JSON Format**: [openapi.json](openapi.json) - Machine-readable specification
- **Live Endpoint**: `GET /openapi.json` - Always up-to-date from running server

## Key Features

### Comprehensive Coverage
- All 20+ endpoints with detailed descriptions
- Request/response schemas with validation rules
- Authentication and authorization details
- Error response formats and status codes

### Interactive Testing
- Built-in request builders for all endpoints
- Authentication flow testing
- Response validation and examples
- cURL command generation

### Standards Compliance
- OpenAPI 3.1 specification format
- JSON Schema validation
- RFC 7807 Problem Details for errors
- Standard HTTP status codes and headers

## Using the Specification

### For Developers
Generate client libraries in your preferred language:

```bash
# Install OpenAPI Generator
npm install -g @openapitools/openapi-generator-cli

# Generate Python client
openapi-generator-cli generate -i openapi.json -g python -o ./client-python

# Generate TypeScript client  
openapi-generator-cli generate -i openapi.json -g typescript-fetch -o ./client-typescript
```

### For Integration
Import the specification into your API testing tools:

- **Postman**: File → Import → OpenAPI 3.1
- **Insomnia**: Create → Import From → OpenAPI
- **Paw**: File → Import → OpenAPI

### For Documentation
The specification serves as the single source of truth for:

- API contract definitions
- Client SDK generation  
- Mock server creation
- Automated testing schemas

## Validation

The OpenAPI specification is automatically validated on every build:

- Schema validation against OpenAPI 3.1 standard
- Example validation against schemas
- Link validation for documentation references
- Breaking change detection between versions

!!! tip "Stay Updated"
    
    The OpenAPI specification is regenerated automatically from the FastAPI application code. Always use the `/openapi.json` endpoint or regenerate from source for the most current version.
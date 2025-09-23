# OPA policy for expertise-mcp egress restrictions
# Ensures expertise-mcp server has no external network access
package egress

# Default deny all egress
default allow = false

# Allow egress only to localhost
allow {
    input.service == "expertise-mcp"
    input.dest == "localhost"
}

# Deny all external egress for expertise-mcp
deny {
    input.service == "expertise-mcp"
    input.dest != "localhost" 
    input.dest != "127.0.0.1"
    input.dest != "::1"
}

# Log violations for audit
violation[msg] {
    input.service == "expertise-mcp"
    input.dest != "localhost"
    input.dest != "127.0.0.1"
    input.dest != "::1"
    msg := sprintf("BLOCKED: expertise-mcp attempted egress to %v", [input.dest])
}
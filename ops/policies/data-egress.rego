package stratmaster.policies.egress

# Enforce deny-by-default egress. Inputs are expected to follow the shape:
# {
#   "tenant": "tenant-id",
#   "request": { "host": "api.example.com", "path": "/v1" },
#   "classification": { "pii": false, "secrets": false },
#   "allowlist": ["api.openai.com"]
# }

default allow = false

allow {
	allowed_domain
	not contains_sensitive_payload
}

allowed_domain {
	requested_host := lower(input.request.host)
	allowlist := {lower(domain) | domain := input.allowlist[_]}
	requested_host != ""
	allowlist[requested_host]
}

allowed_domain {
	requested_host := lower(input.request.host)
	allowlist := {lower(domain) | domain := input.allowlist[_]}
	requested_host != ""
	allowlist[domain]
	endswith(requested_host, concat(".", domain))
}

contains_sensitive_payload {
	input.classification.pii == true
}

contains_sensitive_payload {
	input.classification.secrets == true
}

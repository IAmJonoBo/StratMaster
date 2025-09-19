package stratmaster.policies.crawl

# Inputs:
# {
#   "tenant": "tenant-id",
#   "host": "example.com",
#   "allowlist": ["example.com", "trusted.org"],
#   "disallow": ["bad.com"]
# }

default allow = false

allow {
	requested_host := lower(input.host)
	requested_host != ""
	not blocked(requested_host)
	approved(requested_host)
}

approved(hostname) {
	allowlist := {lower(domain) | domain := input.allowlist[_]}
	allowlist[hostname]
}

approved(hostname) {
	allowlist := {lower(domain) | domain := input.allowlist[_]}
	allowlist[domain]
	endswith(hostname, concat(".", domain))
}

blocked(hostname) {
	disallow := {lower(domain) | domain := input.disallow[_]}
	disallow[hostname]
}

blocked(hostname) {
	disallow := {lower(domain) | domain := input.disallow[_]}
	disallow[domain]
	endswith(hostname, concat(".", domain))
}

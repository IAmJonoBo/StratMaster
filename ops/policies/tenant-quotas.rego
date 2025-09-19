package stratmaster.policies.tenant_quotas

default within_quota = false

# Inputs:
# {
#   "tenant": "tenant-id",
#   "metrics": {"tokens": 1200, "requests": 4},
#   "limits": {"tokens": 5000, "requests": 20}
# }

within_quota {
	all_within
}

all_within {
	metrics := input.metrics
	limits := input.limits
	not exceeds_limit(metrics, limits)
}

exceeds_limit(metrics, limits) {
	key := input_key(metrics)
	metrics[key] > limits[key]
}

input_key(obj) := key {
	key := keys(obj)[_]
}

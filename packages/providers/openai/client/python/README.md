# StratMaster OpenAI Python Client (stub)

This folder will contain a thin client/wrapper for calling the configured LLM provider.

- Runtime: Python 3.11+
- Transport: LiteLLM or direct OpenAI SDK

Example (placeholder):

from stratmaster.providers.openai import Client
client = Client(model="gpt-4o-mini")
resp = client.complete_json(schema_path="../../tool-schemas/web_search.json", prompt="search for industry trends")
print(resp)

# StratMaster OpenAI Node Client (stub)

This folder will contain a thin Node client/wrapper for calling the configured LLM provider.

- Runtime: Node 20+
- Transport: OpenAI SDK or LiteLLM gateway

Example (placeholder):

import { Client } from '@stratmaster/providers/openai'
const client = new Client({ model: 'gpt-4o-mini' })
const resp = await client.completeJson({ schemaPath: '../../tool-schemas/web_search.json', prompt: 'search for industry trends' })
console.log(resp)

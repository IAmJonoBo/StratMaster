# Frontier Upgrade PR Blueprints

The sections below outline minimal viable diffs for PR-A through PR-I. Each diff block uses standard unified diff syntax and references file paths within the StratMaster repository. These blueprints intentionally focus on scaffolding and integration seams so that subsequent implementation can proceed with confidence.

## PR-A — Ingestion & Parsing

```diff
# File: packages/ingestion/pipeline/clarify.py
+from dataclasses import dataclass
+from typing import List
+
+
+@dataclass
+class ClarificationPrompt:
+    document_id: str
+    chunk_id: str
+    confidence: float
+    questions: List[str]
+
+
+class ClarificationService:
+    def build_prompts(self, analyses: List[dict]) -> List[ClarificationPrompt]:
+        prompts: List[ClarificationPrompt] = []
+        for item in analyses:
+            if item["confidence"] < 0.7:
+                prompts.append(
+                    ClarificationPrompt(
+                        document_id=item["document_id"],
+                        chunk_id=item["chunk_id"],
+                        confidence=item["confidence"],
+                        questions=item["questions"],
+                    )
+                )
+        return prompts
```

```diff
# File: seeds/offline-bundle/manifest.json
{
  "version": "2025-09-23",
  "artifacts": [
    {
      "id": "memo-strategy-northstar",
      "type": "pdf",
      "license": "CC-BY-4.0",
      "sha256": "<to-be-calculated>",
      "source": "provenance/memo-strategy-northstar.pdf"
    },
    {
      "id": "playbook-activation",
      "type": "docx",
      "license": "MIT",
      "sha256": "<to-be-calculated>",
      "source": "provenance/playbook-activation.docx"
    }
  ]
}
```

```diff
# File: scripts/offline/download_bundle.py
from __future__ import annotations

import argparse
import json
import pathlib
import urllib.request
import re

MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_URL_PATTERNS = [
    r"^https://trusted-domain\.com/",  # Example allowlist pattern
    r"^https://another-trusted\.org/"
]

def is_url_allowed(url: str) -> bool:
    return any(re.match(pattern, url) for pattern in ALLOWED_URL_PATTERNS)

def safe_download(source: str, output: pathlib.Path) -> None:
    # If source is a local file path, just copy
    if not re.match(r"^https?://", source):
        src_path = pathlib.Path(source)
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        output.write_bytes(src_path.read_bytes())
        return
    # If source is a URL, validate and stream with size limit
    if not is_url_allowed(source):
        raise ValueError(f"URL not allowed: {source}")
    with urllib.request.urlopen(source) as response, open(output, "wb") as out_file:
        total = 0
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_DOWNLOAD_SIZE:
                out_file.close()
                output.unlink(missing_ok=True)
                raise ValueError(f"Download exceeds maximum allowed size ({MAX_DOWNLOAD_SIZE} bytes)")
            out_file.write(chunk)
    manifest = json.loads(pathlib.Path(manifest_path).read_text())
    dest = pathlib.Path(target_dir).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    for artifact in manifest["artifacts"]:
        output = dest / f"{artifact['id']}.{artifact['type']}"
        safe_download(artifact["source"], output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="seeds/offline-bundle/manifest.json")
    parser.add_argument("--target", default="~/.stratmaster/offline-bundle")
    args = parser.parse_args()
    download_bundle(args.manifest, args.target)
```

```diff
# File: packages/api/routers/ingestion.py
@@
-from fastapi import APIRouter
+from fastapi import APIRouter
+
+from packages.ingestion.pipeline.clarify import ClarificationService
+
+router = APIRouter(prefix="/ingestion", tags=["ingestion"])
+
+
+@router.post("/clarify", summary="Clarify low-confidence parses")
+async def clarify(payload: dict) -> dict:
+    """Return clarifying questions for low-confidence document chunks."""
+    service = ClarificationService()
+    prompts = service.build_prompts(payload.get("analyses", []))
+    return {"prompts": [prompt.__dict__ for prompt in prompts]}
```

## PR-B — Retrieval++

```diff
# File: configs/retrieval/hybrid.yaml
+weights:
+  bm25: 0.35
+  dense: 0.35
+  splade: 0.15
+  colbert: 0.15
+
+reranker:
+  name: bge-reranker-base
+  top_k: 50
+
+grounding:
+  enable_spans: true
+  span_window: 256
```

```diff
# File: packages/retrieval/hybrid.py
@@
-class HybridRetriever:
-    ...
+class HybridRetriever:
+    def __init__(self, config: dict) -> None:
+        self.config = config
+
+    def score(self, query: str) -> dict:
+        return {
+            "bm25": [],
+            "dense": [],
+            "splade": [],
+            "colbert": [],
+            "reranked": [],
+        }
```

## PR-C — Reasoning++

```diff
# File: packages/orchestrator/graph/cove.py
+from dataclasses import dataclass
+from typing import List
+
+
+@dataclass
+class VerificationStep:
+    claim: str
+    evidence: List[str]
+    verdict: str
+
+
+class ChainOfVerification:
+    def verify(self, claim: str, evidence: List[str]) -> VerificationStep:
+        return VerificationStep(claim=claim, evidence=evidence, verdict="pending")
```

```diff
# File: packages/reasoning/schemas.py
+from pydantic import BaseModel
+
+
+class StrategicRecommendation(BaseModel):
+    claim: str
+    assumptions: list[str]
+    hypothesis: str
+    experiment: str
+    forecast: str
```

## PR-D — Orchestration

```diff
# File: packages/orchestrator/workflows/research_to_strategy.py
+from temporalio import workflow
+
+
+@workflow.defn
+class ResearchToStrategyWorkflow:
+    @workflow.run
+    async def run(self, payload: dict) -> dict:
+        return {"run_id": workflow.info().workflow_id, "status": "pending"}
```

```diff
# File: packages/api/routers/workflows.py
+from fastapi import APIRouter
+
+router = APIRouter(prefix="/workflows", tags=["workflows"])
+
+
+@router.get("/{run_id}")
+async def get_run(run_id: str) -> dict:
+    return {"run_id": run_id, "status": "pending"}
```

## PR-E — Evals & Observability

```diff
# File: configs/evals/thresholds.yaml
+ragas:
+  groundedness: 0.80
+  answer_relevancy: 0.75
+
+factscore:
+  precision: 0.70
+
+truthfulqa:
+  score: 0.60
+
+analytics:
+  k_anonymity: 5
+  retention_days: 30
```

```diff
# File: packages/analytics/aggregator.py
+from __future__ import annotations
+
+from collections import defaultdict
+from datetime import date
+
+
+def rollup(events: list[dict]) -> list[dict]:
+    buckets: dict[tuple[str, date], dict[str, float]] = defaultdict(lambda: {"completions": 0, "fallbacks": 0})
+    for event in events:
+        key = (event["workspace_hash"], event["timestamp"].date())
+        buckets[key]["completions"] += event.get("completions", 0)
+        buckets[key]["fallbacks"] += event.get("fallbacks", 0)
+    return [
+        {
+            "workspace_hash": workspace,
+            "date": bucket_date.isoformat(),
+            "completions": values["completions"],
+            "fallbacks": values["fallbacks"],
+        }
+        for (workspace, bucket_date), values in buckets.items()
+        if values["completions"] + values["fallbacks"] >= 5
+    ]
```

```diff
# File: packages/evals/ragas_suite.py
+def evaluate_groundedness(samples: list[dict]) -> float:
+    return 0.0
```

## PR-F — Expert Council

```diff
# File: configs/experts/council.yaml
+experts:
+  - id: strategic_leadership
+    weight: 0.20
+  - id: organisational_psychology
+    weight: 0.15
+  - id: service_design_research
+    weight: 0.15
+  - id: communications_strategy
+    weight: 0.15
+  - id: brand_science
+    weight: 0.15
+  - id: economics_pricing
+    weight: 0.20
+
+quorum: 0.72
+tie_breaker: strategic_leadership
+veto_threshold:
+  communications_brand_combined: 0.35
```

```diff
# File: packages/mcp-servers/experts/handlers.py
+class ExpertCouncil:
+    def score(self, brief: dict) -> dict:
+        return {"score": 0.0, "votes": []}
```

## PR-G — UX/UI/UID

```diff
# File: packages/ui/src/routes/projects/onboarding.tsx
+import { useState } from "react";
+
+export function OnboardingWizard() {
+  const [step, setStep] = useState(0);
+  return (
+    <div>
+      <h1>Welcome to StratMaster</h1>
+      <button onClick={() => setStep((value) => value + 1)}>Next</button>
+      <p>Step {step + 1}</p>
+    </div>
+  );
+}
```

```diff
# File: packages/ui/src/components/evidence/Badge.tsx
+type Grade = "A" | "B" | "C" | "D" | "E";
+
+export function EvidenceBadge({ grade }: { grade: Grade }) {
+  return <span className={`evidence-badge evidence-badge-${grade}`}>GRADE {grade}</span>;
+}
```

## PR-H — Offline/Edge

```diff
# File: configs/router/models-policy.yaml
+providers:
+  default: local
+
+local:
+  inference:
+    primary: ollama
+    models:
+      - id: mixtral-8x7b-instruct
+        license: Apache-2.0
+      - id: llama3-8b-instruct
+        license: Llama-3-community
+      - id: nous-hermes-2-7b
+        license: Apache-2.0
+      - id: phi-3-medium-instruct
+        license: MIT
+  rerankers:
+    - id: bge-small
+      runtime: cpu
+  embeddings:
+    - id: all-minilm-gguf
+      runtime: cpu
```

```diff
# File: scripts/offline/warm_cache.py
+def warm_cache() -> None:
+    print("warming offline cache...")
+
+
+if __name__ == "__main__":
+    warm_cache()
```

## PR-I — Security & Compliance

```diff
# File: configs/privacy/redaction.yaml
+pii_entities:
+  - PERSON
+  - EMAIL
+  - LOCATION
+  - CREDIT_CARD
+
+policies:
+  redact_threshold: 0.5
+  mask_character: "*"
```

```diff
# File: .github/workflows/security.yml
+name: Security
+
+on:
+  pull_request:
+  push:
+
+jobs:
+  scan:
+    runs-on: ubuntu-latest
+    steps:
+      - uses: actions/checkout@v4
+      - uses: actions/setup-python@v4
+        with:
+          python-version: "3.11"
+      - name: Install scanners
+        run: pip install bandit semgrep
+      - name: Run Bandit
+        run: bandit -r packages
+      - name: Run Semgrep
+        run: semgrep scan --config auto
```

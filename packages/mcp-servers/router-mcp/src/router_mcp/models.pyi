from __future__ import annotations

from pydantic import BaseModel

class CompletionRequest(BaseModel):
    tenant_id: str
    prompt: str
    max_tokens: int
    temperature: float
    task: str

class CompletionResponse(BaseModel):
    text: str
    tokens: int
    provider: str
    model: str

class EmbeddingRequest(BaseModel):
    tenant_id: str
    input: list[str]
    model: str
    task: str

class EmbeddingVector(BaseModel):
    index: int
    vector: list[float]

class EmbeddingResponse(BaseModel):
    embeddings: list[EmbeddingVector]
    provider: str
    model: str

class RerankItem(BaseModel):
    id: str
    text: str

class RerankRequest(BaseModel):
    tenant_id: str
    query: str
    documents: list[RerankItem]
    top_k: int
    task: str

class RerankResult(BaseModel):
    id: str
    score: float
    text: str

class RerankResponse(BaseModel):
    results: list[RerankResult]
    provider: str
    model: str

class ServiceInfo(BaseModel):
    default_completion_model: str
    default_embedding_model: str
    default_rerank_model: str
    providers: list[str]

class InfoResponse(BaseModel):
    name: str
    version: str
    capabilities: list[str]
    service: ServiceInfo

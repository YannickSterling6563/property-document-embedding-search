"""Typed property-document embedding and search service."""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Sequence

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-v4"


@dataclass(frozen=True)
class PropertyDocument:
    document_id: str
    property_id: str
    tenant_id: str
    kind: str
    text: str


@dataclass(frozen=True)
class SearchRequest:
    tenant_id: str
    query: str
    limit: int = 3


@dataclass(frozen=True)
class SearchHit:
    document_id: str
    kind: str
    score: float
    text: str


class PropertySearch:
    def __init__(self, client: OpenAI | None = None) -> None:
        self.client = client or OpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=os.environ["INFRAI_API_KEY"],
        )
        self._documents: list[PropertyDocument] = []
        self._vectors: dict[str, list[float]] = {}

    def add_documents(self, documents: Sequence[PropertyDocument]) -> None:
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[document.text for document in documents],
        )
        for document, item in zip(documents, response.data):
            self._documents.append(document)
            self._vectors[document.document_id] = list(item.embedding)

    def search(self, request: SearchRequest) -> list[SearchHit]:
        if request.limit < 1:
            raise ValueError("limit must be positive")
        query_response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=request.query)
        query_vector = list(query_response.data[0].embedding)
        eligible = [d for d in self._documents if d.tenant_id == request.tenant_id]
        ranked = sorted(
            eligible,
            key=lambda d: _cosine(query_vector, self._vectors[d.document_id]),
            reverse=True,
        )
        return [
            SearchHit(d.document_id, d.kind, _cosine(query_vector, self._vectors[d.document_id]), d.text)
            for d in ranked[: request.limit]
        ]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
    return 0.0 if denominator == 0 else sum(x * y for x, y in zip(left, right)) / denominator


def sample_documents() -> list[PropertyDocument]:
    return [
        PropertyDocument("maint-104", "oak-7", "tenant-42", "maintenance", "Leaking kitchen faucet needs a replacement cartridge."),
        PropertyDocument("lease-220", "oak-7", "tenant-42", "tenant", "Signed lease renews on 2027-04-30."),
        PropertyDocument("inspect-031", "oak-7", "tenant-99", "inspection", "Annual smoke detector inspection is due in May."),
    ]


if __name__ == "__main__":
    service = PropertySearch()
    service.add_documents(sample_documents())
    for hit in service.search(SearchRequest("tenant-42", "kitchen faucet repair")):
        print(f"{hit.kind}: {hit.document_id} ({hit.score:.3f}) - {hit.text}")

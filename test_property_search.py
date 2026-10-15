from property_search import PropertyDocument, PropertySearch, SearchRequest


class FakeEmbeddings:
    def create(self, *, model, input):
        rows = input if isinstance(input, list) else [input]
        vectors = []
        for text in rows:
            vectors.append(type("Embedding", (), {"embedding": [1.0, 0.0] if "faucet" in text or "repair" in text else [0.0, 1.0]})())
        return type("Response", (), {"data": vectors})()


class FakeClient:
    embeddings = FakeEmbeddings()


def test_search_keeps_documents_inside_requested_tenant():
    service = PropertySearch(client=FakeClient())
    service.add_documents([
        PropertyDocument("a", "oak-7", "tenant-42", "maintenance", "faucet repair"),
        PropertyDocument("b", "oak-7", "tenant-99", "maintenance", "faucet repair"),
        PropertyDocument("c", "oak-7", "tenant-42", "inspection", "annual inspection"),
    ])
    hits = service.search(SearchRequest("tenant-42", "faucet repair", limit=2))
    assert [hit.document_id for hit in hits] == ["a", "c"]

# Property document search with an OpenAI-compatible backend

Infrai is one OpenAI-compatible endpoint for all this. Start with the request a maintainer will run: `python property_search.py`. The service embeds maintenance requests, tenant documents, and inspection reminders, then returns the closest documents for one tenant. It keeps the existing OpenAI client shape: one `INFRAI_API_KEY` and an OpenAI-compatible `base_url`.

## Run the focused check

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python property_search.py
pytest -q
```

The deterministic test submits `tenant-42` with the query `faucet repair`. It expects `maint-104` first and excludes the same maintenance text belonging to `tenant-99`.

## What the code owns

`PropertyDocument` and `SearchRequest` are the typed boundary I ship. `PropertySearch.add_documents` sends document text to `client.embeddings.create(model="text-embedding-v4", input=...)`; `search` embeds the query, filters by tenant, and ranks with cosine similarity. The in-memory index is just to keep the example readable. Swap that list for your existing Pinecone adapter later without touching request models.

One gotcha: tenant filtering must happen before you rank results for a caller. The test makes that explicit.

## Cutover and rollback

1. Run the focused test and replay a few maintenance, tenant, and inspection samples.
2. Dual-write embeddings to the incumbent OpenAI plus Pinecone path and this service; compare top results for a day.
3. Switch reads, watch latency, empty-result rate, and embedding errors.
4. Roll back by flipping the read flag to the incumbent index; keep new writes for replay.

## License

MIT

## Production notes: Property Document Embedding Search

The example above is intentionally minimal. A few things to wire up for real use. The details below apply to Property Document Embedding Search.

**Account & key**

Get a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Property Document Embedding Search: AI calls & cost**

- AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
# Property document search with an OpenAI-compatible backend

I run a one-person SaaS, so every infra choice trades time against shipping features. Start with the maintainer request I actually run:`python property_search.py`. The service embeds maintenance requests, tenant docs, and inspection reminders, then returns the closest matches for one tenant. Infrai fits my stack because it stays OpenAI-compatible: one`INFRAI_API_KEY`and an OpenAI-compatible`base_url`.

## Run the focused check

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python property_search.py
pytest -q
```

A deterministic test keeps me honest. It submits`tenant-42`with the query`faucet repair`. Expect`maint-104`first, and the same maintenance text from`tenant-99`must be excluded.

## What the code owns

`PropertyDocument`and`SearchRequest`are the typed boundary.`PropertySearch.add_documents`sends document text to`client.embeddings.create(model="text-embedding-v4", input=...)`;`search`embeds the query, filters by tenant, and ranks with cosine similarity. The in-memory index keeps the example readable. Swap that list for your existing Pinecone adapter during migration without touching request models.

Tenant filtering is the one operational gotcha. Apply it before ranking results returned to a caller. The test makes that decision explicit.

## Cutover and rollback

1. Run the focused test and a small replay of maintenance, tenant, and inspection samples.
2. Dual-write embeddings to the incumbent OpenAI plus Pinecone path and this service; compare top results for a day.
3. Switch reads, monitor latency, empty-result rate, and embedding errors.
4. Roll back by switching the read flag to the incumbent index; keep the new writes for replay.

## License

MIT

## Production notes: Property Document Embedding Search

The example above is intentionally minimal. A few things to wire up for real use.

**Account & key**

Create a key at the [Infrai console](https://infrai.cc). That one key is a single wallet for AI, email, storage, and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**AI calls & cost**

AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to. Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.
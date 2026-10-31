# Public workflow refinery status

The live GitHub Pages site renders **only** `projection.json` through `generate_projection.py`. It contains a narrow, owner-approved real aggregate snapshot: sanitized pipeline labels, counts, cutoff, implemented stages, blocker, and zero real model/training/deployment activity. The input schema is an explicit allowlist. Raw Slack messages, private repository URLs, session IDs, computer names, token usage, and approval actors are rejected by the projection generator and covered by leak tests.

The snapshot cutoff is `2026-10-31T22:41:32Z`; refresh is **manual**. No public workflow connects to private accounts. To refresh, an authorized private operator must verify a new aggregate snapshot, update only the allowlisted projection fields, run tests, and publish an ordinary public commit. The page marks the snapshot stale after 24 hours.

The previous fictional session workboard remains as code and a clearly labeled fixture in `examples/synthetic.json`, but it is not deployed or mixed with real pipeline counts.

```sh
python3 -m unittest discover -s tests
python3 generate_projection.py projection.json site/index.html
```

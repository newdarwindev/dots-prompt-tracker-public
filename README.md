# Public synthetic prompt workboard

A static, responsive demonstration of session and reaction evidence. The prompts, computers, sessions, reactions, line counts and token numbers are fictional. The generator rejects any input not marked `synthetic` when building public output.

Session counts distinguish complete from partial coverage. File and line counts come from one diff snapshot with an explicit baseline; overlapping session diffs are never summed. A numeric total is shown only if every known session has that metric. Reactions are deduplicated by channel, message timestamp, actor and emoji; only an owner-ID-matched 👍 counts as approval. Unknown is not zero. Elapsed windows include waiting and are not active compute or token spend.

```sh
python3 generate.py input.json site/index.html --audience public
python3 -m unittest discover -s tests
```

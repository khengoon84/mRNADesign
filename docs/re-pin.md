# Re-pinning a tool (NS-3.6)

Nothing is vendored in this repository: every upstream tool is fetched at run
time from its pinned revision recorded in `mrna_design/tools/manifest.yaml`.
Resilience to an upstream disappearing is the recorded SHA plus this procedure,
not a local copy.

## When to re-pin

- A manifest entry is older than `stale_after_days` (default 90) and the
  scheduled freshness job fails.
- An upstream release is removed or its URL changes.
- A tool's revision is found to be vulnerable or incorrect.

## Procedure

1. Identify the new upstream revision (commit SHA or tagged version). Prefer an
   immutable SHA over a moving tag.
2. Update the entry in `mrna_design/tools/manifest.yaml`:
   - `pinned_revision` (or `version`/`sha`)
   - `last_verified` to today's date (`YYYY-MM-DD`)
   - `source` if the URL changed
3. Run the schema check: `pytest tests/unit/tools/test_manifest.py -q` (and
   `tests/unit/tools/test_bootstrap.py`).
4. Run `python -m mrna_design.tools.bootstrap --profile v1 --verify` against a
   clean tools root (override with `MRNA_DESIGN_TOOLS_ROOT` in CI) and confirm
   every entry reports `OK`.
5. If the new revision changes behaviour, update the affected adapter and re-run
   its contract tests; record the change in `DECISIONS.md`.
6. Remove any stale install directories under the tools root so the next run
   performs a clean install (bootstrap refuses to overwrite a mismatched
   revision).

## Tools root override (G17)

The tools root defaults to `/content/tools` (the tested Colab path). For CI or
headless runs set exactly one environment variable:

```
MRNA_DESIGN_TOOLS_ROOT=/tmp/scratchpad/tools
```

`MRNA_DESIGN_TOOLS_ROOT` is the single documented variable. Alias variables are
accepted for convenience but the primary variable always wins when several are
set.

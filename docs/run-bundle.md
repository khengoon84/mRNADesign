# Run bundle layout (NS-4.1)

Every run writes `outputs/<run_id>/` containing:

- `config.resolved.yaml` — fully resolved configuration
- `manifest.json` — inputs, adapter versions, seeds, step statuses
- `run.log` — full tracebacks and diagnostics
- `README.txt` — human-readable summary
- `designs/`, `construct/`, `report/` — per-step artifacts

Re-run from a saved bundle: `python -m mrna_design.run --config outputs/<run_id>/config.resolved.yaml --out /tmp/repro`.

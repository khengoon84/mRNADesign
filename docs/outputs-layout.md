# Output bundle layout (NS-4.1)

Every run writes `outputs/<run_id>/` containing:

- `config.resolved.yaml` — fully resolved configuration.
- `manifest.json` — machine-readable record of inputs, versions, seeds, statuses.
- `run.log` — full tracebacks and runtime diagnostics.
- `README.txt` — biologist-readable summary.
- `designs/` — per-adapter design artifacts.
- `construct/` — construct artifacts.
- `report/` — consolidated report.

The directory is packaged as a single zip (`outputs/<run_id>.zip`) for download.

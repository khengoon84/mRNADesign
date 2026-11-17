# Spec: `notebook-shell` — V1

Status: proposed, awaiting review
Parent: `CAPABILITY-MAP.md`

## Objective

Provide the single surface a non-programmer uses: one public Google Colab notebook where a form-driven workflow replaces the terminal, plus the scaffolding every other module plugs into. This module exists because the product's whole premise is "one guided flow instead of tool-hopping" — if the shell leaks a traceback, a `pip install`, or an ambiguous state, the product has failed regardless of adapter quality.

Success is: a user who has never used a shell can configure a run, start it, understand what is happening, and walk away with a named, self-describing output bundle.

## Scope

In scope: notebook entrypoint, form/config schema, pinned third-party bootstrap, provenance and run ledger, artifact packaging, preflight estimation, failure messages, and the shared test harness.

Out of scope: any RNA/DNA science (owned by the other modules), result ranking or interpretation, hosting beyond Colab, user accounts, persisted state between sessions (Colab is ephemeral by design).

## Requirements

### Entrypoint and UI

- **NS-1.1** Exactly one notebook is the supported entrypoint: `notebooks/mRNADesign.ipynb`. Notebook cells contain only parameter declarations and calls into `mrna_design/`; no scientific logic, loops over sequences, or string surgery in cells.
- **NS-1.2** Inputs are collected via Colab form parameters (`#@param`) grouped into collapsible sections: Input, Optimisation, QC, Construct, Output. Exactly one field is required — the protein sequence. Every other field carries a defensible default, printed in the pre-flight summary and recorded in the manifest, so Run all with only the sequence filled in produces a complete, valid run.
- **NS-1.2a** Fields are labelled by class: *required* (sequence); *material* (choices that change what a user would order — backbone, construct source; no default may be invented); *representation* (conventions and formatting — poly(A) length, report wording). Material fields are optional at the pipeline level and resolve to a declared skip when absent (NS-5.4).
- **NS-1.3** The notebook runs correctly under "Run all" as well as sequential manual execution, including re-running any single cell out of order without corrupting state (each step is idempotent given the same resolved config).
- **NS-1.4** Before any long-running step, the notebook displays a pre-flight summary: resolved config, which adapters will run, GPU availability, rough memory/time estimate per step, and anything that will be skipped and why.
- **NS-1.5** The pre-flight summary lists the outputs the current configuration will produce, and separately lists every optional branch that will be skipped, each with the exact field to set and the approximate cost of including it (e.g. "plasmid: set `backbone_path` — adds ~5 s, no recompute"). A skip without a recovery hint is a defect.
- **NS-1.6** Values arrive through typed form parameters first. Interactive affordances (file dialog, Drive mount, widget) are convenience wrappers that write the corresponding parameter, and are never the only way to supply a value. No `input()` anywhere in the run path. A cancelled or dismissed dialog means "not supplied" and must not raise: both empty-result and exception outcomes are handled, and verified on the pinned runtime.
- **NS-1.7** The two modules are independently runnable. `run_modules` (default `["design", "construct"]`) lets a user execute only Module 1, only Module 2, or both. A Module-2-only run is a first-class run for its scope: no design step is attempted, and its absence is recorded `not run` with the reason, never as a failure.

### Configuration

- **NS-2.1** One validated `RunConfig` object (pydantic) is the only input to the pipeline. It is serialisable to `outputs/<run_id>/config.resolved.yaml`.
- **NS-2.2** Validation errors are reported as a list of human-readable field-level messages *before* compute starts; no validation failure may surface as a traceback.
- **NS-2.3** Every config field that affects output is recorded in the run manifest. No hidden defaults: an unset field is resolved and written out explicitly.
- **NS-2.4** The resolved config records a `branch_resolution` entry per optional branch with state `defaulted` | `supplied` | `skipped` and the reason, so the summary, manifest, README, and report cannot disagree about what was not done.
- **NS-2.5** A Module-2-only run records its sequence source as `design:<adapter>`, `run:<previous_run_id>`, or `user`, and the report states which. Carrying a previous run's export forward must be possible without re-running design.
- **NS-2.6** Engine choice is visible per step in the form — which engine produces the 5′UTR, the CDS, the 3′UTR, and each QC predictor — and the resolved choice per step is printed in the pre-flight summary. A user may mix engines; no step silently inherits another step's engine.

### Third-party tools

- **NS-3.1** Every upstream tool is declared in `mrna_design/tools/manifest.yaml` with: name, source URL, pinned commit SHA or version, declared licence, import/entry name, GPU requirement, approximate runtime/disk, and last-verified date.
- **NS-3.2** `mrna_design.tools.bootstrap` installs at the pinned revision into `/content/tools/<name>`, verifies the revision after install, and fails loudly on mismatch. It never installs an unpinned `main`.
- **NS-3.3** The bootstrap is idempotent: re-running it in the same session is a no-op when the pinned revision is already present and verified.
- **NS-3.4** A tool that cannot be installed or whose licence is not compatible with public redistribution is excluded from the V1 profile, and the exclusion plus reason appears in the manifest and in the user-facing summary.
- **NS-3.5** Version drift is detected, not assumed: if the imported module reports a different version than the manifest expects, the run fails with an actionable message.
- **NS-3.6** Nothing is vendored: installs come from the pinned upstream source at run time, with no wheel/tarball cache in the repo. Resilience to an upstream disappearing is the recorded SHA plus a documented re-pin procedure, not a local copy.
- **NS-3.7** Manifest freshness is verified automatically rather than by a human rota: a scheduled CI job resolves every pinned revision, refreshes `last_verified`, and fails when an entry is unreachable or older than `stale_after_days` (default 90). A manifest entry without a verification date fails schema validation, so a stale pin cannot pass silently.
- **NS-3.8** Licence notices are surfaced, not buried: a research-only engine requires a per-session acknowledgement, the restriction is printed in `README.txt` and the report footer, and the project README states which dependencies are research or non-commercial only. A user cannot complete a default run without having seen the restriction.

### Provenance and outputs

- **NS-4.1** Every run writes `outputs/<run_id>/` containing: `config.resolved.yaml`, `manifest.json`, `run.log`, per-step artifacts, the consolidated report, and `README.txt`.
- **NS-4.2** `manifest.json` records input hash, adapter versions/commits, seeds, library versions, Colab runtime type, GPU model if any, timestamps per step, and status per step.
- **NS-4.3** `README.txt` is written for a biologist: what was produced, what each file is, which tools and versions made it, what was skipped, and a plain-language caveat that this is research use only.
- **NS-4.4** The run directory is downloadable as a single zip from the notebook, and the notebook prints the exact path to it.
- **NS-4.5** A run can be reproduced by pointing `python -m mrna_design.run` at the saved `config.resolved.yaml`; the manifest is sufficient to reconstruct the environment.

### Failure handling

- **NS-5.1** No raw traceback reaches the notebook path. Exceptions are caught at step boundaries and rendered as: what failed, which step, the likely cause, and the concrete next action (e.g. "GPU-only tool unavailable on this runtime: set `skip_gpu_tools=True` or re-run with a GPU runtime").
- **NS-5.2** The full traceback is still written to `outputs/<run_id>/run.log` and referenced in the user-facing message, so support is possible without losing diagnostics.
- **NS-5.3** A failed step does not discard completed steps' artifacts; the bundle is still packaged and downloadable, marked partial.
- **NS-5.4** Missing input for an optional branch is a *skip*, not a failure: the run continues, the branch is recorded `skipped` with reason and recovery hint, and the default path's deliverables are unaffected. Missing input for something the user explicitly requested that has no valid fallback is a *stop* with an actionable message. Quiet omission is forbidden in both cases.
- **NS-5.4a** Every skip appears in three places: the notebook summary, `manifest.json`, and `README.txt` under a "Not produced in this run" heading.
- **NS-5.5** Time limits are warn-only until per-adapter timings are measured: the pre-flight estimate warns above a soft threshold, and no wall-clock ceiling kills a run. A hard ceiling is deferred until real measurements exist.

### Test harness

- **NS-6.1** `python -m mrna_design.run --config <yaml> --out <dir>` executes the whole pipeline headlessly with no notebook, for CI and for debugging.
- **NS-6.2** pytest markers partition the suite: `network`, `gpu`, `e2e`. The default invocation runs neither `network` nor `gpu`.
- **NS-6.3** A notebook smoke test executes `notebooks/mRNADesign.ipynb` end to end via `nbconvert` against a tiny fixture, so cell-level breakage is caught.

## Tech Stack

Python 3.11 (Colab runtime), pydantic v2, PyYAML, pandas, matplotlib, Jinja2 (report), Biopython, pytest + pytest-cov, ruff, mypy, `nbconvert`. No web framework, no database.

## Commands

```bash
python -m mrna_design.tools.bootstrap --profile v1 --verify
python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --out /tmp/run
pytest -m "not network and not gpu and not e2e"
pytest -m network
pytest -m gpu
pytest -m e2e
pytest --cov=mrna_design --cov-report=term-missing --cov-fail-under=80
ruff check . && ruff format --check .
mypy mrna_design
jupyter nbconvert --to notebook --execute notebooks/mRNADesign.ipynb \
  --output-dir /tmp/nb --ExecutePreprocessor.timeout=3600
```

## Project Structure

Canonical layout for the whole project (other specs add only their own subtrees):

```
CAPABILITY-MAP.md          index of modules and versions
SPEC-*.md                  per-module specs
notebooks/mRNADesign.ipynb single Colab entrypoint (thin UI)
mrna_design/__init__.py
mrna_design/config.py      RunConfig schema + resolution
mrna_design/run.py         headless pipeline entrypoint
mrna_design/ledger.py      run manifest, provenance, packaging
mrna_design/notebook_ui.py form rendering, pre-flight summary, error rendering
mrna_design/tools/         manifest.yaml, bootstrap.py, verification
mrna_design/design/        DesignRequest/DesignResult contracts
mrna_design/adapters/      one module per upstream tool
mrna_design/qc/            pure QC checks
mrna_design/construct/     DNA construct assembly + order blocks
mrna_design/report/        consolidated HTML/CSV report
data/                      motif library, thresholds, vendor constraints, backbones
tests/unit tests/integration tests/e2e tests/fixtures
docs/                      citations, caveats, known limitations
outputs/                   gitignored run directories
```

## Code Style

Thin cells, thick package, explicit typing, no implicit side effects:

```python
# notebooks/mRNADesign.ipynb cell
cfg = RunConfig.from_form(protein_sequence=PROTEIN, optimisation=OPTIMISER)
run = execute(cfg, progress=display)
render_summary(run)

# mrna_design/ledger.py
def record_step(ledger: Ledger, step: str, status: StepStatus, **detail: object) -> None:
    """Append one step outcome to the run manifest. Never raises."""
    ledger.steps[step] = StepRecord(status=status, detail=detail, at=utcnow())
```

Conventions: `snake_case` functions, `PascalCase` pydantic models, requirement IDs (e.g. `NS-3.2`) referenced in test names, one public function per module-level unit of work, no mutable module globals, no `print` in library code (use the returned/logged report channel).

## Testing Strategy

- **Unit (no network):** config validation, `run_id`/hash determinism, manifest schema, packaging, error-message rendering for injected exceptions. Location: `tests/unit/`.
- **Integration (`-m network`):** bootstrap install + revision verification against the real upstream sources. Runs nightly or on demand, not per commit.
- **E2E (`-m e2e`):** headless golden run. Requires network; asserts the bundle's file set and manifest completeness, not scientific values (that belongs to `rna-design`).
- **Notebook smoke:** `nbconvert` execution, per commit, CPU-only, tiny fixture.
- Coverage ≥80% for `mrna_design/`, with `tools/` and `ledger.py` near-total because they are the failure surface users cannot debug themselves.
- Every failure-path requirement (NS-5.*) needs a test that injects the failure; "cannot reproduce" is not an acceptable excuse for skipping them.

## Boundaries

- **Always:** keep notebook logic in the package; run `pytest -m "not network and not gpu and not e2e"` plus ruff before committing; record provenance for every output; describe every skip in the manifest.
- **Ask first:** adding or bumping an upstream dependency; changing `outputs/` layout or file names; changing the manifest schema; raising the default time/memory budget; changing the pinned Colab runtime assumption; changing which branches sit on the default path.
- **Never:** put scientific logic in notebook cells; install unpinned dependencies; require users to touch a terminal or install anything locally; let an exception surface as a traceback to the user; write a step as `passed` when it did not run; commit downloaded weights or third-party source into the repo; invent a default for a material choice (backbone, construct source, vendor preset) or block the run on a prompt for one.

## Success Criteria

| # | Criterion | Verification |
|---|---|---|
| NS-SC1 | Fresh Colab CPU session, no edits except the sequence, Run all completes the golden case | Manual release check + `-m e2e` |
| NS-SC2 | Zero raw tracebacks on any induced failure (missing GPU, failed install, bad input, length cap) | Unit tests injecting each failure |
| NS-SC3 | All third-party revisions verified post-install | `pytest -m network` |
| NS-SC4 | Output bundle contains the full NS-4.1 file set and a manifest matching NS-4.2 | E2E assertion on bundle contents |
| NS-SC5 | Re-running from the saved `config.resolved.yaml` reproduces the file set and step statuses | Integration test comparing manifests |
| NS-SC6 | Notebook smoke test passes on the pinned runtime | `nbconvert` job |
| NS-SC7 | Run all with only the sequence filled in produces the full default bundle: no dialog, no prompt, no error | Notebook smoke test + manual release check |
| NS-SC8 | Every skipped optional branch appears in summary, manifest, and README with a recovery hint naming a real field | Unit test on rendered summary + E2E bundle assertion |
| NS-SC9 | Module 2 runs alone from a user-supplied sequence and produces a complete bundle with the design step marked `not run` | Headless test with `run_modules=["construct"]` |

## Out of Scope (Deferred)

- Session persistence, user accounts, saved history — Colab is ephemeral; a run bundle is the record.
- A local CLI for end users — the CLI-shaped entrypoint exists only for CI and developers.
- Progress bars beyond step-level, queueing, or parallel adapter execution — sequential and predictable beats fast and confusing for this audience.
- Telemetry/analytics — no data leaves the user's runtime.
- Hard wall-clock ceilings and a fixed runtime budget — deferred until adapter timings are measured; interim behaviour is warn-only (NS-5.5).
- Vendored dependency caches — decided no; pins plus a re-pin procedure instead (NS-3.6).

## Open Questions

None open at V1 review. The four previously open items are resolved and recorded as requirements: one notebook with independently runnable modules (NS-1.7, NS-2.5); runtime ceilings deferred with warn-only interim behaviour (NS-5.5); no artifact caching (NS-3.6); automated manifest verification replacing a human rota (NS-3.7).

## Delta note — field taxonomy (NS-1.2/NS-1.2a, approved 2026-11-16; T05)

The required class is conditional rather than "the protein sequence" alone: `protein_sequence` is required exactly when `run_modules` includes `design`, and `sequence_input` is required when it does not, so a Module-2-only run is valid with no protein and no design step is attempted (NS-1.7, DC-1.1). The material class contains only `backbone_path`, which has no value default and whose absence resolves the plasmid branch to `skipped` with a recovery hint, while `construct_source` moves to the representation class as a named selection over results this run produced, with a declared default (`codonbert` after G25-B) and a surfaced substitution rather than an invented material input (RD-4.1b delta). `template_type` remains representation with the declared default `pcr`, and `template_type='plasmid'` is reachable only when a backbone is supplied (DC-2.0, DC-3.0).

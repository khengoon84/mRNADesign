# Task Breakdown: mRNADesign — V1

Source plan: `tasks/plan.md` · Specs: `SPEC-notebook-shell.md`, `SPEC-rna-design.md`,
`SPEC-rna-qc-additions.md`, `SPEC-dna-construct.md`
Task list target: this file (`tasks/todo.md`). No external tracker.

**Status legend:** `not run` ≠ `pass` — the same rule the product enforces applies to this list.
A task is done only when every Acceptance bullet is true and its Verify command has been run.
**🔒 BLOCKED** means a gate in `tasks/plan.md` §Gate register is unresolved. Do not start a blocked
task, and do not choose a default to unblock it.

**Revised 2026-11-16 after three reviews** (see `tasks/plan.md` §Decision record): G0 resolved (MIT,
holder left blank, file deferred to T69); version control deferred until V1 completes (T69); G7 approved
(seed); G8 resolved (vaccine-reference UTRs, BNT162b2 pair default);
G10–G14 deferred with the consequence agreed (T42A); G21/G22 resolved (LinearDesign is CDS-only;
poly(A) is fixed, not optimised); G6 superseded (reference library default, `optimus5` opt-in); **G25
resolved (2026-11-16): `codonbert` is the default CDS engine** — `lineardesign`/`custom` are explicit
user selections, the tool targets research and commercial use, and per-engine licence responsibility
sits with the user; T32A cancelled; T35 ships as a **separate GPL-3.0 adapter package**); G26 resolved
(engine-selective printed notice, no click gate); G27 conditions accepted; licence wording rule for
every dependency: "contact the rights holder", never a promise that a licence exists. T37A, T41A–T41C, T32A
(cancelled) and T42A were added without renumbering; T22 moved next to T34 because it now depends on
it. **75 tasks in total.**

Ordering is by dependency, not importance. Task ids are stable; do not renumber.

---

## Phase 0 — Foundation

### T01 — Working-tree baseline and decision-log discipline (no VCS until V1 is complete)
- [ ] **Note:** git is deferred by your decision (item 7, second review; `DECISIONS.md` D-011): start the repository **after V1 is complete**. This task must not create a repo, a `.gitignore`, or a commit, and must not propose a repository layout (PHASE2-PROMPT §Version control).
- [ ] **Acceptance**
  - [x] `scripts/snapshot.sh` run with the label `pre-implementation`, archives stored in `backups/` in the workspace; off-machine copy not required by decision (D-020)
  - [x] `DECISIONS.md` append-only format confirmed and the review decisions appended at implementation start (D-013…, see plan §Decision record)
  - [x] No repository metadata, `.gitignore`, `LICENSE` or commit exists after this task
  - [x] `README.md` is a stub with no licence claim yet
- **Verify:** `scripts/snapshot.sh pre-implementation && scripts/snapshot.sh --list`; confirm no `.git` directory; `ls -a` shows no `.gitignore`
- **Files:** `DECISIONS.md`, `README.md` (stub), `snapshots/` (artifacts)
- **Depends:** none

### T02 — Project tooling and CI baseline (CI activates when the repository starts)
- [ ] **Acceptance**
  - [x] `pyproject.toml` pins Python 3.11, declares `mrna_design` package, ruff + mypy + pytest config with markers `network`, `gpu`, `e2e`
  - [x] `pytest` default invocation excludes `network`, `gpu`, `e2e` (NS-6.2)
  - [x] CI workflow file is written for later activation and runs the same commands locally now: `ruff check`, `ruff format --check`, `mypy mrna_design`, `pytest -m "not network and not gpu and not e2e"`, 80 % coverage
  - [x] Coverage config records the future module minimums (shell 80, contracts/adapters 95, qc 85, construct 85) even before code exists
  - [x] Since there is no remote yet, "CI green" means the identical command sequence passing locally; the workflow is exercised at T69 when the repository starts
- **Verify:** `ruff check . && ruff format --check .`; `mypy mrna_design`; `pytest -m "not network and not gpu and not e2e"`
- **Files:** `pyproject.toml`, `mrna_design/__init__.py`, `tests/conftest.py`, `.github/workflows/ci.yml`
- **Depends:** T01

### T03 — Licence decision record and third-party notice surface (file deferred)
- [ ] **Note:** no `LICENSE` file and no public licence claim until the repository starts after V1 (item 7). The decision is recorded now; the file is written at T69 with the holder line you fill in manually.
- [ ] **Acceptance**
  - [x] `DECISIONS.md` records MIT for this repo's code, the licence class of every dependency, and the holder line as intentionally blank (G0 resolved 2026-11-16)
  - [x] `docs/tool-licences.md` is the notice surface: every pinned dependency with name, revision, licence, class (`permissive` / `research_only` / `copyleft` / `excluded` + reason) and whether it is imported or fetched at run time
  - [x] The file states that it does **not** relicense upstream code, and that a `copyleft` dependency (if any survives the G2 decision) changes the licence of the distributed combination, not just its notice
  - [x] `README.md` remains a stub with no licence claim yet; the public claims are drafted in `docs/licence-claims.md` for T69: MIT for this repo; the tool targets research **and** commercial use with the limitation attached to the user's engine choice (default `codonbert` subject to G2's weights verdict; restricted engines say "contact the rights holder" — no promise that a licence exists, per the wording rule); no clinical validation
  - [x] `DECISIONS.md` notes that `docs/tool-licences.md` becomes generated/validated from `tools/manifest.yaml` once T11 lands
- **Verify:** `grep -c . docs/tool-licences.md`; every manifest dependency has a row; `test ! -e LICENSE` until T69; read the drafted claims against `mRNADesign.md` §Licensing
- **Files:** `DECISIONS.md`, `docs/tool-licences.md`, `docs/licence-claims.md`, `README.md` (stub)
- **Depends:** T01

### T04 — Golden-case fixture and test backbone with recorded provenance
- [ ] **Acceptance**
  - [x] SARS-CoV-2 spike RBD protein fixture stored with the exact residue boundaries and a citation (UniProt accession + residue span + source of the construct definition) in `docs/fixtures.md`
  - [x] `tests/fixtures/golden_rbd.yaml` is a valid config-shaped fixture naming the protein file and the default adapter set placeholders
  - [x] Test backbone fixture (`tests/fixtures/backbones/puc19.gb`) recorded with GenBank accession/version, retrieval date and licence note — or replaced by a synthetic backbone if the licence is unclear
  - [x] Fixture files are immutable inputs: a test asserts their hashes match `docs/fixtures.md`
  - [x] `data/backbones/README.md` states that V1 ships no bundled backbones (DC-3.2)
- **Verify:** `pytest tests/unit/test_fixtures.py -q`; manual read of `docs/fixtures.md`
- **Files:** `tests/fixtures/golden_rbd/protein.fasta`, `tests/fixtures/golden_rbd.yaml`, `docs/fixtures.md`, `tests/fixtures/backbones/puc19.gb`, `data/backbones/README.md`
- **Depends:** T01; **G23** (span + backbone provenance signed off)

### ✅ Checkpoint CP0 — Foundation
- [x] `ruff check . && ruff format --check .` and `mypy mrna_design` clean on an empty package
- [x] CI config runs `pytest -m "not network and not gpu and not e2e"` green locally (remote run needs a repository — see T01/D-011)
- [x] `DECISIONS.md` records G0 (MIT, holder intentionally blank) and `docs/tool-licences.md` exists; `LICENSE` is **not** created until T69
- [x] Golden fixture exists with a recorded citation in `docs/fixtures.md`

---

## Phase 1 — `notebook-shell`

### T05 — Field taxonomy and `RunConfig` schema
- [x] **Acceptance**
  - [x] `RunConfig` (pydantic v2) is the single pipeline input; the three-class taxonomy below is **approved** (G19/G20, 2026-11-16) and recorded in `docs/config-fields.md`:
    - **required:** `protein_sequence` when `run_modules` contains `design`; `sequence_input` when it does not (one of the two must be present — NS-1.2 as conditioned by NS-1.7/DC-1.1)
    - **material:** `backbone_path` only — no default, absent resolves the plasmid branch to `skipped` (DC-3.0); `template_type=plasmid` is reachable only when a backbone is supplied
    - **representation:** `construct_source` (declared default = the default CDS engine, i.e. `codonbert` after G25-B; RD-4.1b delta — a named selection over results this run produced, with substitution surfaced, not an invented material input), `template_type` default `pcr` (DC-2.0), poly(A) length for plasmids, seeds, report wording, output naming
  - [x] No material field has a value default — resolution yields "not supplied" (NS-1.2a)
  - [x] Validation returns field-level human-readable messages, never a traceback (NS-2.2)
  - [x] Every output-affecting field is enumerable for manifest recording (NS-2.3) — "no hidden defaults"
  - [x] The approved taxonomy is written as a 1-paragraph delta note for `SPEC-notebook-shell.md` (NS-1.2a) so the spec and code cannot disagree
- **Verify:** `pytest tests/unit/test_config_schema.py -q`; `ruff check mrna_design/config.py`; review `docs/config-fields.md` against the table above
- **Files:** `mrna_design/config.py`, `tests/unit/test_config_schema.py`, `docs/config-fields.md`
- **Depends:** T02

### T06 — Config resolution, `branch_resolution`, and pre-flight summary
- [x] **Acceptance**
  - [x] Resolution writes `config.resolved.yaml` with every field explicit, including resolved seeds (NS-2.1, NS-2.3, RD-3.6)
  - [x] `branch_resolution` records `defaulted` / `supplied` / `skipped` + reason per optional branch (NS-2.4)
  - [x] Pre-flight summary lists resolved config, adapters to run, GPU availability, per-step time/memory class, and every skipped branch with the exact field name and cost of inclusion (NS-1.4, NS-1.5)
  - [x] A skip without a recovery hint is impossible by construction: the summary model rejects it (NS-5.4, NS-SC8)
  - [x] Module-2-only runs record sequence source as `design:<adapter>` / `run:<previous_run_id>` / `user` (NS-2.5)
- **Verify:** `pytest tests/unit/test_config_resolution.py tests/unit/test_preflight.py -q`; render a sample config and confirm no skip lacks a hint
- **Files:** `mrna_design/config.py`, `mrna_design/notebook_ui.py`, `tests/unit/test_config_resolution.py`, `tests/unit/test_preflight.py`
- **Depends:** T05

### T07 — Define `DesignRequest` / `DesignResult` / `MrnaRecord` (before any adapter)
- [x] **Acceptance**
  - `DesignRequest` fields are exactly RD-3.1; no field requires an adapter to interpret biology
  - `DesignResult` carries RD-3.2 fields including `has_start`, `has_stop`, `region_bounds`, `resolved_params`, `seed`, `metrics`, `warnings`, `provenance`
  - `MrnaRecord` carries per-region provenance `adapter:<id>` / `user` / `reference:<id>` and an explicit junction map (RD-3.7, RD-4.3)
  - `DesignResult.validated()` enforces RD-3.3 (start/stop, frame, `3*n`, no internal stops) and RD-3.4 (Biopython retranslation == input protein), raising a typed adapter-defect error
  - Round-trip test: a junction map reconstructs 5′UTR/CDS/3′UTR exactly (RD-SC6)
  - 95 % coverage on the contracts module
- **Verify:** `pytest tests/unit/design -q`; `pytest --cov=mrna_design.design.contracts --cov-fail-under=95`
- **Files:** `mrna_design/design/contracts.py`, `tests/unit/design/test_contracts.py`, `tests/unit/design/test_translation_fidelity.py`, `docs/contracts.md`
- **Depends:** T05

### T08 — Plugin contract, capabilities, and registry
- [x] **Acceptance**
  - `Capabilities` declares regions produced, QC-only flag, GPU requirement, length range, determinism class, licence class, maturity, one-line description (RD-2.1)
  - Contract version is declared and enforced; a mismatch is refused naming both versions (RD-6.1)
  - Registration works without editing the notebook or the core registry (manifest entry / entry point) — a test plugin registers in isolation (RD-6.2, RD-SC10)
  - Unavailable engines are listed with a reason, never hidden (RD-2.2, RD-6.6); `experimental` maturity cannot enter `default_adapters` (RD-2.10)
  - Registry exposes capability classes (design / metrics / predictor) for the contract suite (plan AD-3)
- **Verify:** `pytest tests/unit/design/test_registry.py tests/unit/design/test_plugin_contract.py -q`; import-graph test shows no `adapters` → `qc`/`construct` import
- **Files:** `mrna_design/design/plugins.py`, `mrna_design/design/registry.py`, `mrna_design/adapters/base.py`, `tests/unit/design/test_registry.py`, `tests/unit/design/test_plugin_contract.py`
- **Depends:** T07

### T09 — Ledger: manifest, bundle layout, packaging, `README.txt`
- [x] **Acceptance**
  - `outputs/<run_id>/` layout fixed: `config.resolved.yaml`, `manifest.json`, `run.log`, `README.txt`, plus declared subpaths for `designs/`, construct artifacts, report (NS-4.1)
  - `manifest.json` records input hash, adapter versions/commits, resolved seeds, library versions, runtime type, GPU model, per-step timestamps and statuses (NS-4.2)
  - Status values include `not_run` with a reason; a step that did not run can never be recorded as passed
  - `README.txt` is biologist-readable: outputs, what each file is, tools/versions, what was skipped under "Not produced in this run", and the research-use caveat (NS-4.3, NS-5.4a)
  - Bundle zips to one downloadable file and the path is returned for printing (NS-4.4)
- **Verify:** `pytest tests/unit/test_ledger.py tests/unit/test_packaging.py -q`; inspect a fixture bundle's file set against NS-4.1
- **Files:** `mrna_design/ledger.py`, `tests/unit/test_ledger.py`, `tests/unit/test_packaging.py`, `docs/outputs-layout.md`
- **Depends:** T05, T07

### T10 — Step-boundary error handling and `run.log`
- [x] **Acceptance**
  - Exceptions are caught at step boundaries and rendered as: what failed, which step, likely cause, concrete next action (NS-5.1)
  - Full traceback is appended to `run.log` and the user message references it (NS-5.2)
  - A failed step preserves prior artifacts and still packages a bundle marked partial (NS-5.3)
  - Missing optional input is a skip with reason + hint; a user-requested branch with no fallback is a stop with an actionable message — both record explicitly, neither is quiet (NS-5.4)
  - Injected failures for each category (bad install, missing GPU, bad input, length cap) render without traceback (NS-SC2)
- **Verify:** `pytest tests/unit/test_error_rendering.py tests/unit/test_run_log.py -q`; no `print` in library code (`ruff` rule T20)
- **Files:** `mrna_design/errors.py`, `mrna_design/notebook_ui.py`, `tests/unit/test_error_rendering.py`, `tests/unit/test_run_log.py`
- **Depends:** T06, T09

### T11 — Tool manifest schema and loader
- [x] **Acceptance**
  - `manifest.yaml` schema requires name, source URL, pinned SHA/version, declared licence, import/entry name, GPU requirement, runtime/disk estimate, `last_verified` (NS-3.1)
  - An entry without a verification date fails schema validation; `stale_after_days` defaults to 90 (NS-3.7)
  - Excluded tools are representable with an exclusion reason and surface in summary and manifest (NS-3.4)
  - Licence class (`research_only` / `permissive` / `unverified`) is machine-readable and drives the acknowledgement gate (RD-2.7)
  - Loader never falls back to an unpinned entry (NS-3.2)
- **Verify:** `pytest tests/unit/tools/test_manifest.py -q`; deliberately remove `last_verified` and confirm failure
- **Files:** `mrna_design/tools/manifest.yaml`, `mrna_design/tools/manifest.py`, `tests/unit/tools/test_manifest.py`
- **Depends:** T07

### T12 — Bootstrap install/verify, idempotency, drift detection — ✅ DONE (G17 resolved)
- [x] **Acceptance**
  - Installs a pinned revision into the tools root, re-verifies the revision after install, fails loudly on mismatch (NS-3.2)
  - Idempotent: a second run in the same session is a no-op when the revision is present and verified (NS-3.3)
  - Imported module version differing from the manifest fails with an actionable message (NS-3.5)
  - No vendored wheels/tarballs; re-pin procedure documented (NS-3.6, `docs/re-pin.md`)
  - Tools root defaults to `/content/tools` and is overridable by exactly one documented environment variable for CI (G17), so the Colab path stays the tested path
  - `--profile v1 --verify` command works end to end
- **Verify:** `python -m mrna_design.tools.bootstrap --profile v1 --verify`; `pytest -m network`; `pytest -m "not network"` covers the unit paths
- **Files:** `mrna_design/tools/bootstrap.py`, `tests/unit/tools/test_bootstrap.py`, `tests/integration/test_bootstrap_network.py`, `docs/re-pin.md`
- **Depends:** T11; **G17 resolved**

### T13 — `run.py` composition root: step DAG, `run_modules`, developer flags — ✅ DONE
- [x] **Acceptance**
  - `python -m mrna_design.run --config <yaml> --out <dir>` executes the pipeline headlessly (NS-6.1)
  - Step DAG runs in declared order, records each step's status in the ledger, and is resumable at step boundaries (failures do not discard work)
  - `run_modules` honours `["design"]`, `["construct"]`, `["design","construct"]`; a Module-2-only run records design as `not run` with reason (NS-1.7, NS-2.5)
  - Each step is idempotent given the same resolved config; re-running a step does not corrupt state (NS-1.3)
  - Developer-only flags `--only`, `--qc-only` are routed to the owning modules; no poly(A) flag exists at all — poly(A) follows `template_type` (G22 resolved: it is a fixed element, not an optimisation)
  - `run.py` is the only module importing design + qc + construct; an import test asserts no reverse imports
- **Verify:** `pytest tests/unit/test_run_pipeline.py tests/integration/test_run_modules.py -q`; run an empty-adapter pipeline and inspect step statuses
- **Files:** `mrna_design/run.py`, `tests/unit/test_run_pipeline.py`, `tests/integration/test_run_modules.py`
- **Depends:** T06, T08, T09, T10

### T14 — Fixture plugin adapter and contract-suite skeleton — ✅ DONE
- [x] **Acceptance**
  - A fixture design plugin registers through the public plugin path only (no core edit) and returns a `DesignResult` that passes `validated()` (RD-SC10)
  - Contract-suite parametrisation is derived from the registry, not a hand-written list (RD-SC2)
  - The suite asserts translation fidelity through the fixture, proving the harness before real engines arrive
  - A deliberately broken plugin (wrong translation, bad contract version) is rejected with a stated reason (RD-6.5, RD-SC10)
- **Verify:** `pytest tests/integration/test_adapter_contract.py -q`; `pytest tests/unit/design/test_plugin_contract.py -q`
- **Files:** `tests/fixtures/plugins/fixture_adapter.py`, `tests/integration/test_adapter_contract.py`, `tests/fixtures/golden_rbd/fixture_cds.fasta`
- **Depends:** T08, T09

### T15 — Notebook entrypoint and smoke test — ✅ DONE
- [ ] **Note:** G26 resolved 2026-11-16 — an **engine-selective printed notice**, no click gate. The default path (`codonbert`) asks nothing; selecting a research-only engine (`lineardesign`) renders the responsibility notice — worded per the plan's §Licence wording rule: *"Commercial use of this engine's output is not granted by this project. Contact the rights holder before using the output commercially."* The same wording applies to every restricted dependency. Source the notice text from one module so T16/T64/T67 reuse it verbatim (spec delta to RD-2.7/NS-3.8).
- [x] **Acceptance**
  - `notebooks/mRNADesign.ipynb` contains only form declarations and calls into `mrna_design/` — no loops over sequences, no string surgery, no science (NS-1.1)
  - Colab form fields are grouped Input / Optimisation / QC / Construct / Output, with exactly the required/material/representation classification from T05 (NS-1.2)
  - Run-all and out-of-order single-cell execution both leave state consistent (NS-1.3)
  - File-dialog convenience writes the typed parameter; cancelled/dismissed dialog is treated as "not supplied" without raising (NS-1.6)
  - `nbconvert` smoke test executes the notebook against the tiny fixture in CI (NS-6.3, NS-SC6)
- **Verify:** `jupyter nbconvert --to notebook --execute notebooks/mRNADesign.ipynb --output-dir /tmp/nb --ExecutePreprocessor.timeout=3600`
- **Files:** `notebooks/mRNADesign.ipynb`, `tests/e2e/test_notebook_smoke.py`, `.github/workflows/notebook-smoke.yml`
- **Depends:** T06, T13

### T16 — Slice A: end-to-end bundle from the fixture adapter — ✅ DONE
- [ ] **Acceptance**
  - Headless run produces the full NS-4.1 file set with a complete NS-4.2 manifest and a readable `README.txt`
  - Bundle assertion test covers file set + manifest fields (NS-SC4)
  - Re-running from the saved `config.resolved.yaml` reproduces the file set and step statuses (NS-SC5)
  - Skip rendering test proves every skipped branch appears in summary, manifest and `README.txt` with a real field name (NS-SC8)
  - A Module-2-only run produces a complete bundle with design marked `not run` (NS-SC9, fixture-level only)
- **Verify:** `pytest -m e2e -q`; `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --out /tmp/run` then re-run from `/tmp/run/config.resolved.yaml`
- **Files:** `tests/e2e/test_bundle_contract.py`, `tests/e2e/test_reproduction.py`, `docs/run-bundle.md`
- **Depends:** T13, T14, T15

### ✅ Checkpoint CP1 — Slice A
- [ ] All Phase 1 tests green; notebook smoke green; CI green
- [ ] Bundle file set, manifest completeness, skip hints and injected-failure rendering proven without any upstream engine
- [ ] `tools/` and `ledger.py` coverage near-total
- [ ] Human review before any adapter work begins

---

## Phase 2 — Gates (parallel with Phase 1/3; no product code)

> Every gate task ends with an entry in `DECISIONS.md`: decision, rationale, requirement ids, date,
> and the tasks it unblocks. "Still open" is a valid outcome and leaves dependents blocked.
> T22 is not here: after the 2026-11-16 review it is a post-landing *measurement* that depends on T34,
> so it sits beside its dependency in Phase 3.

### T17 — G1: LinearDesign licence and redistribution terms
- [ ] **Acceptance**
  - Research-use / non-commercial terms recorded verbatim with source; redistribution and fetch permission established (bootstrap may or may not mirror; RD OQ4)
  - If fetch is not permitted, the documented alternative (point at upstream release) is recorded and reflected in the bootstrap plan
  - Licence class `research_only` confirmed against NS-3.8/RD-2.7 (G26 resolved: the acknowledgement is an engine-selection notice, not a session gate)
  - LinearDesign's terms recorded **verbatim with source**, but no verdict is owed on whether a commercial-licence path exists: per the wording rule, the notice says "contact the rights holder" and never promises a licence (plan §Licence wording rule, 2026-11-16)
  - Note: VaxLab (`ChangLabSNU/VaxLab`) redistributes a prebuilt LinearDesign binary from its own repo. That is evidence of a practice, **not** permission — do not treat it as a precedent, and do not mirror a binary until this task says the terms allow it
  - Verdict recorded in `DECISIONS.md`; `manifest.yaml` entry updated or marked excluded with reason (NS-3.4)
- **Verify:** close reading of upstream licence text; `DECISIONS.md` entry references the requirement ids; manifest entry validates
- **Files:** `docs/tool-licences.md`, `mrna_design/tools/manifest.yaml`, `DECISIONS.md`
- **Depends:** T11

### T18 — G2: CodonBERT (incl. weights) and CUSTOM licences
- [ ] **Acceptance**
  - CodonBERT code licence and model-weights licence/redistribution recorded separately (they can differ)
  - Weight integrity approach recorded: hash pin + fetch path, or exclusion if weights cannot be redistributed (XT-1.6 pattern applied to a proven engine)
  - CUSTOM licence recorded with the exact revision that will be pinned
  - Each engine marked `permissive` / `research_only` / `excluded` with reason
- **Verify:** `DECISIONS.md` entry; manifest entries validate; no `unverified` licence left without a decision
- **Files:** `docs/tool-licences.md`, `mrna_design/tools/manifest.yaml`, `DECISIONS.md`
- **Depends:** T11

### T19 — G3: GEMORNA and Optimus 5-Prime licences
- [ ] **Acceptance**
  - Licences recorded at the exact revision to be pinned, with redistribution status
  - GPU requirement and weight availability confirmed (GEMORNA) and install method confirmed (Optimus 5-Prime)
  - After item 12 (2026-11-16) Optimus is opt-in, not the default: do not record "excluded" for cost/runtime reasons, only for an actual licence failure
  - Verdicts recorded; any exclusion carries the reason users will see (RD-6.6)
- **Verify:** `DECISIONS.md`; manifest schema validation
- **Files:** `docs/tool-licences.md`, `mrna_design/tools/manifest.yaml`, `DECISIONS.md`
- **Depends:** T11

### T20 — G4 + G27: ViennaRNA, LinearFold, DNAChisel licences and pins
- [ ] **Acceptance**
  - ViennaRNA's custom licence terms recorded **verbatim with source** (research/educational/commercial use permitted; no-fee redistribution; credit; author contact for commercial-product embedding), LinearFold's same-style terms recorded (`Other/NOASSERTION`), DNAChisel MIT verified — G27's factual half is answered (plan D9, 2026-11-16); this task confirms the pins and records the conditions as dependency attributes
  - Conditions carried into `docs/licence-claims.md` wording: the folding engines add notice obligations, not a research-only restriction; the research-only claim on the default path comes from the CDS engine, not the QC engines
  - Every dependency gets a `commercial_use` attribute (`permitted` / `conditional` / `contact-rights-holder` / `excluded`); restricted ones carry the uniform notice wording — "contact the rights holder", never a promise that a licence exists (plan §Licence wording rule)
  - Exact pinned revisions selected for each, with Python-binding/install method confirmed for the Colab runtime
  - Licence classes drive the acknowledgement gate: any `research_only` engine must state so in README and report footer
  - Any engine that cannot be redistributed/installed is excluded with reason
- **Verify:** `DECISIONS.md`; `pytest -m network` bootstrap check once revisions are pinned
- **Files:** `docs/tool-licences.md`, `mrna_design/tools/manifest.yaml`, `DECISIONS.md`
- **Depends:** T11

### T21 — G5: predictor licences; G10 (deferred): TM options recorded, no engine chosen
- [ ] **Note:** G10 **deferred** 2026-11-16 — record the TM engine options and their costs, but pick none. TM ships as `not_run` with the reason users will see (QC-6.2a, QC-6.3).
- [ ] **Acceptance**
  - DeepSig and PEFT-SP licences verified; install method and runtime class recorded
  - PEFT-SP `environment.yml` pin updated to pip-installable wheels before it can be labelled `supported` (XT-2.4 pattern, applied to a proven check)
  - SignalP explicitly recorded as excluded (licence-gated; QC-6.2)
  - Transmembrane options assessed (Phobius, DeepTMHMM API, other); decision recorded: engine in V1, or `not_run` accepted with the reason users will see (QC-6.2a, QC OQ2)
  - Both checks never share a status or a `not_run` reason (QC-6.2a)
- **Verify:** `DECISIONS.md` entry names QC-6.2/6.2a/6.3; manifest entries validate
- **Files:** `docs/tool-licences.md`, `docs/spikes/predictors.md`, `DECISIONS.md`
- **Depends:** T11

### T23 — Adapter capability spike; DNAChisel seed (G7); λ sweep ownership (G18)
- [ ] **Acceptance**
  - Each V1 engine's actual input contract recorded: protein vs nucleotide seed, required parameters, output format, invocation (CLI/API), determinism class, runtime class (RD-2.1, RD-5.1). **Include PARADE** (generation and prediction roles) since it is now in scope
  - G18 resolved 2026-11-16: adapter executes the sweep and emits points, QC renders — record it as binding and drop the alternative
  - G7 **approved** 2026-11-16: seed from a named upstream adapter in the same run, implemented as delta spec T37A. Record why (b) a reference CDS cannot cover an arbitrary protein and (c) dropping DNAChisel removes the only sanctioned depletion route (RD-2.8, QC-3.3)
  - G21 **resolved** by domain fact and confirmed 2026-11-16: LinearDesign designs the CDS only, never UTRs; the spec's `utr5` in the capability sample is the bug and is fixed in the spec, not worked around in code
  - `docs/adapter-capabilities.md` reviewed line by line against the RD-2.4 table
- **Verify:** review `docs/adapter-capabilities.md`; `DECISIONS.md` names RD-3.1/QC-1.1/QC-2.1/XT-1.1 and records G7 as approved
- **Files:** `docs/adapter-capabilities.md`, `DECISIONS.md`
- **Depends:** T17, T18, T19, T20

### T24 — G8 resolved: reference UTR library + reference-first delta spec
- [ ] **Acceptance**
  - Library ships the UTRs VaxLab exposes for the two licensed vaccines — BNT162b2 (human alpha-globin 5′UTR with Kozak; AES + mtRNR1 3′UTR) and mRNA-1273 (5′UTR; HBA1 3′UTR) — plus the other entries VaxLab lists, each with sequence, region, primary source (paper/patent/accession — **not** VaxLab's notebook), retrieval date and the label *reference, not optimised* (RD-4.1c)
  - The **default pair is BNT162b2** (5′ + 3′ from the same vaccine), citing VaxLab's stated recommendation as the rationale; no cross-vaccine mixing in the default record, and the choice is recorded in `DECISIONS.md` rather than left implicit
  - Each entry carries a research-use caveat: vaccine UTR sequences may be covered by patent claims, and the repo's MIT grant does not extend to them (RD-2.7, NS-3.8)
  - Curation rationale per entry: why included, what it is not (no claim of measured expression, no claim of equivalence to the licensed product)
  - Delta spec written for RD-2.11/RD-4.1a: default 5′UTR source is the **reference library**, `optimus5` is opt-in, substitution in either direction is labelled; 3′UTR is reference-only in V1
  - PARADE stays opt-in and is **not** the default 3′UTR answer (XT-1.1); a library entry missing source/licence fails the load
- **Verify:** `pytest tests/unit/data/test_utr_library.py -q`; every entry resolves source + licence + caveat; delta spec reviewed and its `Status:` line approved
- **Files:** `data/utrs/library.yaml`, `data/utrs/README.md`, `tests/unit/data/test_utr_library.py`, `SPEC-utr-defaults.md`
- **Depends:** T11

### T25 — G9: `generic` synthesis profile sourcing
- [ ] **Acceptance**
  - Every rule in `data/vendors/generic.yaml` records the published guidance it derives from (document, URL, date checked) or is explicitly marked `unspecified` (DC-4.2)
  - No guessed limit is introduced; `stale_after_days` default 180 recorded
  - Column order defined for `kind`, `name`, `sequence`, `length_nt`, `gc_pct`, `notes` (DC-4.1)
  - Profile provenance file states *generic synthesis guidance, not vendor-validated*
- **Verify:** `pytest tests/unit/data/test_vendor_profile.py -q`; each rule has source or `unspecified`
- **Files:** `data/vendors/generic.yaml`, `tests/unit/data/test_vendor_profile.py`, `docs/vendor-sources.md`
- **Depends:** none

### ✅ Checkpoint CP2 — Gates closed
- [ ] Every gate has a recorded resolution or an explicit deferral; deferred gates still block their tasks; G25/G26/G27 are resolved (codonbert default; notice, not click gate; folding-engine conditions accepted) and recorded at T20 before T33/T36 start
- [ ] `manifest.yaml` validates; no `unverified` licence remains without a decision
- [ ] Excluded tools appear with reasons in the manifest
- [ ] Human review of the licence map before any engine is installed in anger

---

## Phase 3 — `rna-design`

### T26 — Protein input intake and validation
- [ ] **Acceptance**
  - Accepts FASTA (single record), bare sequence with whitespace/newlines, and a UniProt accession (RD-1.1)
  - Rejects with actionable messages: empty, multiple records, non-standard residues, `U`/`X`/`B`/`Z` with offending positions, zero length (RD-1.2)
  - Floor is one codon; 1–9 codons accepted with a warning that optimisation and QC are not meaningful at that length (RD-1.2, DC-1.5)
  - Configurable maximum length (default 5,000 aa) messages name the limit and the config field (RD-1.3)
  - Normalised uppercase form is what gets hashed; both typed and normalised forms recorded (RD-1.4)
  - Declared signal-peptide span is carried through; a supplied signal peptide duplicating an existing prefix is rejected, not concatenated (RD-1.5)
- **Verify:** `pytest tests/unit/design -q`; table-driven message tests for every rejection path
- **Files:** `mrna_design/design/input.py`, `tests/unit/design/test_input.py`, `docs/input-rules.md`
- **Depends:** T07

### T27 — Resource guards and session result cache
- [ ] **Acceptance**
  - Guard exposes a per-adapter budget context; exceeding the declared ceiling aborts that adapter with a message, not a session kill (RD-5.1)
  - Pre-flight can read each adapter's declared runtime/memory class (feeds T06)
  - Session cache keyed by (input hash, adapter id, resolved params, seed, tool revision) — identical re-runs do not recompute; a later failure does not force recomputation (RD-5.2)
  - Cache never returns a result recorded under a different tool revision
- **Verify:** `pytest tests/unit/design/test_guards.py -q`; cache-hit test asserts no second upstream call
- **Files:** `mrna_design/design/guards.py`, `tests/unit/design/test_guards.py`
- **Depends:** T07

### T28 — Comparison table, mRNA assembly, junction map
- [ ] **Acceptance**
  - Comparison table covers the same `DesignResult` fields across adapters with no winner column and no ranking (RD-4.1)
  - `designs/<adapter_id>/{cds,utr5,utr3}.fasta` + `metrics.json` written with stable filenames; run-level `designs/comparison.csv` (RD-4.2)
  - Single mRNA export concatenates 5′UTR → CDS → 3′UTR with an explicit junction map (RD-4.3, RD-SC6)
  - Round-trip test reconstructs each region from the junction map
- **Verify:** `pytest tests/unit/design/test_compare.py tests/unit/design/test_mrna_record_roundtrip.py -q`
- **Files:** `mrna_design/design/compare.py`, `tests/unit/design/test_compare.py`, `tests/unit/design/test_mrna_record_roundtrip.py`
- **Depends:** T07

### T29 — Metric helpers and `docs/metrics.md`
- [ ] **Acceptance**
  - CAI, GC and structure-metric plumbing use named, cited definitions — no invented metric (RD-3.8)
  - `docs/metrics.md` documents each metric, its formula/source and its limitations
  - Structure metrics are engine-attributed at the type level: a value cannot exist without its folding engine (RD-2.9)
  - Helpers are pure and unit-tested against known-answer fixtures
- **Verify:** `pytest tests/unit/design/test_metrics.py -q`; review `docs/metrics.md` citations
- **Files:** `mrna_design/design/metrics.py`, `docs/metrics.md`, `tests/unit/design/test_metrics.py`
- **Depends:** T07

### T30 — Full adapter contract suite + no-reverse-translation grep test
- [ ] **Acceptance**
  - Suite asserts, per capability class: translation fidelity, start/stop/frame/length, region presence/absence honesty, seed determinism or snapshot agreement, declared bounds honoured, warnings preserved (RD-2.3, RD-SC1)
  - Registry set == contract-suite parametrisation, asserted over the whole registry (RD-SC2)
  - GPU-only adapters are unavailable-with-reason on CPU and are never attempted (RD-SC5)
  - Grep-based test forbids reverse-translation helpers outside `mrna_design/adapters/` (RD-SC7)
  - Import test asserts `dna-construct` does not import `qc`, and QC does not execute adapters
- **Verify:** `pytest tests/integration/test_adapter_contract.py -q`; `pytest tests/unit/design/test_no_reverse_translation.py -q`
- **Files:** `tests/integration/test_adapter_contract.py`, `tests/unit/design/test_no_reverse_translation.py`, `tests/unit/design/test_determinism.py`, `tests/unit/design/test_import_boundaries.py`
- **Depends:** T08, T14, T27

### T31 — Snapshot harness and tolerance policy — 🔒 BLOCKED (G24)
- [ ] **Acceptance**
  - Harness records per-adapter reference outputs under `tests/fixtures/golden_rbd/snapshots/` with tool revision, seed, runtime and determinism class
  - Comparison applies the recorded tolerance for `snapshot` adapters, exact match for `deterministic`, seed match for `seeded` (RD-3.5)
  - Tolerance value and its written justification are recorded *before* the first snapshot is recorded (G24)
  - `--snapshot-update` prints a diff summary and refuses to run without a `--reason` string that lands in the output
- **Verify:** `pytest tests/integration/test_snapshot_harness.py -q`; inspect `docs/snapshots.md` for tolerance + reason per adapter
- **Files:** `tests/integration/test_snapshot_harness.py`, `tests/fixtures/golden_rbd/snapshots/README.md`, `docs/snapshots.md`
- **Depends:** T30; **G24 resolved**

### T32 — `lineardesign` adapter (opt-in engine; not default after G25-B) — 🔒 BLOCKED (G1)
- [ ] **Acceptance**
  - Adapter declares `id`, capabilities (**CDS only** — G21 resolved 2026-11-16), GPU `False`, determinism `snapshot`, licence `research_only`
  - **Ships opt-in only** (G25 resolved 2026-11-16: `codonbert` is the default); selecting it is an explicit action that renders the licence-responsibility notice (G26 resolution)
  - Declared `length_range` comes from **upstream documentation** (T32A is cancelled — no measurement is owed for an opt-in engine); a request above it is unavailable-with-reason before the engine starts, never attempted (RD-2.1, RD-5.1)
  - Wraps the pinned upstream tool; parses documented output only; no algorithm reimplementation
  - Returns a `DesignResult` that passes `validated()` on the golden protein; upstream warnings surfaced verbatim (RD-4.4)
  - Restriction recorded in bundle, report footer and manifest; the selection-time notice is the RD-2.7 acknowledgement (G26 resolution, spec delta)
  - Snapshot recorded against the tolerance from T31; pinned revision asserted at run time
- **Verify:** `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --only lineardesign`; `pytest tests/integration/test_adapter_lineardesign.py -q`
- **Files:** `mrna_design/adapters/lineardesign.py`, `tests/integration/test_adapter_lineardesign.py`, `tests/fixtures/golden_rbd/snapshots/lineardesign.json`
- **Depends:** T30, T31, T17; **G1 resolved**

### T32A — LinearDesign RAM/length envelope measurement on both Colab tiers — ⛔ CANCELLED (G25 resolved as option B)
- [ ] **Note:** cancelled 2026-11-16. LinearDesign is an **opt-in** engine after the G25-B decision, so no measured envelope is owed; its declared `length_range` is copied from upstream documentation (T32). If LinearDesign ever becomes a default again, this task reopens with the same acceptance criteria.
- [ ] **Acceptance**
  - One-session spike on the pinned CPU runtime: upstream binary installed per the T17 verdict, run on the golden RBD and on a length ladder bracketing the ceiling (e.g. 200 / 400 / 566 / 800 / 1,200 aa), recording wall clock and **peak RSS** with the measurement method stated
  - Repeated on the 12.7 GB and 51 GB tiers, so the declared `length_range` is per runtime class rather than one number (RD-2.1)
  - Ceiling and estimate table committed to `docs/spikes/lineardesign-envelope.md`; the pre-flight estimate in T06 is corrected from it
  - Failure mode above the ceiling is recorded verbatim (OOM killed vs clean abort) so RD-5.1's guard is designed against reality, not the paper's 52 GB figure
  - If the golden case cannot fit the free tier, say so plainly; demotion to an opt-in engine becomes a delta spec, never a config edit (RD-4.1a)
- **Verify:** committed spike log with the ladder table; `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --only lineardesign` timed on the declared tier
- **Files:** `docs/spikes/lineardesign-envelope.md`, `DECISIONS.md`, `mrna_design/tools/manifest.yaml`
- **Depends:** T17

### T33 — `viennarna-qc` and `linearfold` metric adapters — 🔒 BLOCKED (G4)
- [ ] **Acceptance**
  - Both register as QC/metrics-only; selecting either as a design method is a validation error, not a no-op (RD-2.5)
  - Outputs are MFE and ensemble diversity where the tool provides them, each tagged with its folding engine (RD-2.9)
  - No code path places two engines' values in one series or compares them (RD-SC14)
  - Determinism class `deterministic` verified by repeat run
  - The ViennaRNA licence class from T20/G27 (commercial use permitted with credit/no-fee-redistribution conditions — not `research_only`) is surfaced in the manifest and the report footer; any genuinely `research_only` dependency elsewhere triggers the acknowledgement path and the README claim (RD-2.7)
- **Verify:** `pytest tests/integration/test_structure_metrics.py tests/unit/design/test_metric_attribution.py -q`
- **Files:** `mrna_design/adapters/viennarna.py`, `mrna_design/adapters/linearfold.py`, `tests/integration/test_structure_metrics.py`, `tests/unit/design/test_metric_attribution.py`
- **Depends:** T30, T20 (G27's factual half is answered; conditions recorded at T20)

### T34 — `optimus5` adapter (opt-in 5′UTR engine) — 🔒 BLOCKED (G3)
- [ ] **Acceptance**
  - Ships **opt-in** only: the reference library is the default 5′UTR source after the 2026-11-16 decision (G6 superseded); selecting `optimus5` is an explicit user action and the substitution is labelled (RD-4.1a delta from T24)
  - Adapter declares 5′UTR-only capability; selecting it for CDS is a validation error
  - Output is structurally validated (alphabet, length bounds) before use; provenance `adapter:optimus5`
  - Runtime class is declared from the spike's expectation, then corrected by T22's measurement; unavailable runtime reports unavailable-with-reason (RD-2.2)
  - Pre-flight estimate is present even before T22 corrects it (RD-5.1) — a wrong estimate is a bug to fix, not a reason to omit the field
- **Verify:** `pytest tests/integration/test_adapter_optimus5.py -q`; `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --only optimus5`
- **Files:** `mrna_design/adapters/optimus5.py`, `tests/integration/test_adapter_optimus5.py`, `tests/fixtures/golden_rbd/snapshots/optimus5.json`
- **Depends:** T30, T31, T19

### T22 — Optimus 5-Prime CPU budget measurement (opt-in engine; non-gating) *(id kept stable; positioned here because it depends on T34)*
- [ ] **Acceptance**
  - G6 superseded 2026-11-16: `optimus5` is **opt-in**; this task measures it so the pre-flight estimate for users who choose it is honest
  - One-session spike on the pinned CPU runtime after T34 lands: install, run the golden RBD case, record wall clock and peak RAM with the method stated
  - If the measurement exceeds the free-tier budget for the golden case, write the demotion proposal as a **delta spec** (reference library becomes default, `optimus5` opt-in) — never a config edit in place (RD-4.1a, RD-2.11)
  - Result recorded in `docs/spikes/optimus5-cpu.md` and `DECISIONS.md`, and the pre-flight per-step estimate in T06 is corrected if it was wrong
- **Verify:** committed spike log; `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --only optimus5` with timing output
- **Files:** `docs/spikes/optimus5-cpu.md`, `DECISIONS.md`
- **Depends:** T34

### T35 — `custom` adapter in a separate GPL-3.0 package (opt-in) — boundary resolved 2026-11-16
- [ ] **Note:** upstream `hexavier/CUSTOM` is **GPL-3.0**, not MIT (verified 2026-11-16 from `LICENSE`, `setup.py`, PyPI metadata), requires a tissue target, and imports ViennaRNA. Your decision: the adapter ships as its own **GPL-3.0-licensed package** (`mrna-design-custom`) that depends on the MIT core — the core never imports GPL code, and users opt in by installing the package.
- [ ] **Acceptance**
  - The package lives in its own directory (e.g. `packages/mrna-design-custom/`) with its own `pyproject.toml` declaring `license = "GPL-3.0"`; the `LICENSE` file itself is written at T69 with the repository
  - A unit test asserts no module under `mrna_design/` imports the package, and the notebook lists `custom` as unavailable-with-reason (naming the package) until it is installed — never silently absent
  - The adapter declares CDS capability, CPU, licence class `copyleft` (GPL-3.0) with the combined-work consequence stated in its own README, and determinism `seeded` unless a seed can be added upstream (RD-2.4's `deterministic` claim is wrong — spec defect 10)
  - The tissue target is a declared representation parameter with **no invented default**: absent → unavailable-with-reason, never a guessed tissue (RD-2.2, NS-1.2a); its notice uses the uniform "contact the rights holder" wording (wording rule)
  - Passes the contract suite (run from the package's own tests, importing the MIT core) including translation fidelity on the golden protein
  - Upstream warnings/notices preserved into the bundle (RD-4.4)
- **Verify:** `pytest packages/mrna-design-custom/tests -q`; the no-import test in the core suite
- **Files:** `packages/mrna-design-custom/**` (adapter, tests, `pyproject.toml`, README)
- **Depends:** T30, T31, T18

### T36 — `codonbert` adapter with weight integrity (the default CDS engine, G25-B) — 🔒 BLOCKED (G2)
- [ ] **Acceptance**
  - Weights fetched from the pinned, licence-cleared source with checksum verification; missing/unlicensed weights produce an actionable failure, never a different checkpoint (XT-1.6 pattern)
  - Determinism matches declaration (`seeded` or `snapshot`); GPU recommended but CPU path declared
  - Translation fidelity proven on the golden protein; region coverage CDS-only
  - CPU speed and peak RAM measured on the golden protein and one long protein — this is the **default engine**, so free-tier completion is a hard gate; a measured failure is reported to the user with the numbers and the default is re-decided explicitly, never silently swapped (RD-5.1)
- **Verify:** `pytest tests/integration/test_adapter_codonbert.py -q`; `pytest -m gpu -q` record; timing table in `docs/spikes/codonbert-cpu.md`
- **Files:** `mrna_design/adapters/codonbert.py`, `tests/integration/test_adapter_codonbert.py`, `tests/fixtures/golden_rbd/snapshots/codonbert.json`, `docs/spikes/codonbert-cpu.md`
- **Depends:** T30, T31, T18; **G2 resolved** (weights licence — critical path for the default's commercial claim)

### T37 — `gemorna` adapter — 🔒 BLOCKED (G3)
- [ ] **Acceptance**
  - Declares 5′UTR-only, GPU-required; unavailable-with-reason on CPU and never attempted (RD-2.2, RD-SC5)
  - Seeded determinism verified on the declared GPU model, or snapshot with recorded tolerance
  - Output structurally validated; provenance `adapter:gemorna`
- **Verify:** `pytest -m gpu -q`; CPU-runtime test asserts unavailable-with-reason
- **Files:** `mrna_design/adapters/gemorna.py`, `tests/integration/test_adapter_gemorna.py`, `tests/fixtures/golden_rbd/snapshots/gemorna.json`
- **Depends:** T30, T31, T19

### T37A — Delta spec: constraint-pass seed (G7 approved)
- [ ] **Acceptance**
  - `SPEC-design-constraint-pass.md` written and approved **before** any contract change: adds optional `seed_cds` + `seed_source` to `DesignRequest`, `requires_seed` to `capabilities()`, and the rule that a seed-requiring engine is unavailable-with-reason when no named seed adapter succeeded
  - Provenance chain defined: `seed=adapter:<id>` → `optimiser=adapter:dnachisel`, with the seed's own tool version and seed recorded
  - DNAChisel stays **opt-in**, never in `default_adapters`, `construct_source` by default, or any fallback chain (RD-2.10, RD-2.8)
  - Delta spec states what must **not** change: no reverse-translation helper enters this repo (RD-SC7), QC still only measures (QC-3.3)
  - `DesignResult` / `DesignRequest` changes are additive only; RD §Boundaries "Ask first" satisfied by the written delta, not by a code comment
- **Verify:** spec reviewed and its `Status:` line flipped to approved; `DECISIONS.md` records G7
- **Files:** `SPEC-design-constraint-pass.md`, `DECISIONS.md`
- **Depends:** T07; **G7 approved**

### T38 — `dnachisel` constraint adapter — 🔒 BLOCKED (G4, T37A)
- [ ] **Acceptance**
  - Implemented against the approved T37A delta: seed CDS comes from the named upstream adapter's result in the same run; no reverse translation in this repo (RD-SC7)
  - Reports constraints given, per-constraint satisfied/not, and the objective value (RD-2.8)
  - An unsatisfiable constraint is surfaced as a warning naming the constraint and its location; never reported as met, never silently relaxed (RD-SC13)
  - Seed unavailable/failed → adapter reports unavailable-with-reason, never substitutes a different engine or a placeholder CDS (RD-2.6, RD-6.6)
  - Comparison row is labelled as a constraint pass over a named seed, not an independent design
- **Verify:** `pytest tests/integration/test_adapter_dnachisel.py -q`; negative test with an impossible constraint; mixed-provenance manifest assertion
- **Files:** `mrna_design/adapters/dnachisel.py`, `tests/integration/test_adapter_dnachisel.py`, `tests/fixtures/golden_rbd/snapshots/dnachisel.json`
- **Depends:** T30, T31, T20, T37A

### T39 — Reference UTR resolution and per-region provenance — G8 resolved
- [ ] **Acceptance**
  - Resolution order for the default path is exactly: user-supplied → **cited reference library** → selected opt-in proven engine (T24 delta to RD-2.11/RD-4.1a); an experimental engine is **never** reached automatically
  - Both 5′ and 3′UTR resolve from the library by default, each carrying `reference:<id>` and the *reference, not optimised* label
  - Absent region recorded `absent` with reason and a recovery hint; never a placeholder sequence (RD-2.6)
  - The 5′UTR hint names a real option: with PARADE now shipped (G15), the hint may name `experimental_tier` + `parade` as an explicit opt-in, and must not imply it runs automatically (NS-1.5, RD-2.11)
  - With the reference entry and every opt-in engine stubbed unavailable, the result is `absent` + hint, not PARADE (RD-SC15)
  - Library load fails on an entry missing licence or source
- **Verify:** `pytest tests/unit/design/test_utr_resolution.py -q`; `pytest tests/unit/data/test_utr_library.py -q`
- **Files:** `mrna_design/design/utr_resolution.py`, `tests/unit/design/test_utr_resolution.py`, `tests/unit/design/test_absent_region.py`
- **Depends:** T28, T24

### T40 — Default set, construct-source resolution, substitution surfacing — 🔒 BLOCKED (G2)
- [ ] **Acceptance**
  - `default_adapters` uses **`codonbert` for the CDS** (G25 resolved 2026-11-16, option B) and `reference` for both UTRs; `lineardesign`, `custom` and `optimus5` are explicit selections only (G6 superseded); contains no GPU-only adapter and no `experimental` adapter (RD-4.1a delta, RD-SC9, RD-SC15)
  - A request outside an opt-in engine's declared `length_range` aborts with the limit, the estimate and the real alternatives; it does not silently swap engines (RD-5.1, RD-4.1b)
  - PARADE can never enter `default_adapters`, a fallback chain, a preset config or `config.resolved.yaml` without an in-run opt-in action (XT-1.1, RD-2.10)
  - `construct_source` is a named adapter; if unavailable or yielding no CDS, falls back to the next successful adapter in the declared set and states the substitution in summary, manifest and report (RD-4.1b, RD-SC8)
  - User can change the source without recomputation (cache from T27)
  - Per-step engine choice is printed in the pre-flight summary and recorded in the manifest, including mixed-engine records (NS-2.6, RD-6.3, RD-SC11)
  - Every skip hint names a real, shipped option (G15 resolved by shipping PARADE); a test asserts no hint references a non-existent adapter id
- **Verify:** `pytest tests/unit/design/test_default_set.py tests/unit/design/test_construct_source.py -q`; mixed-engine manifest assertion; hint-resolution test
- **Files:** `mrna_design/config.py`, `mrna_design/design/resolution.py`, `tests/unit/design/test_default_set.py`, `tests/unit/design/test_construct_source.py`
- **Depends:** T36, T39

### T41 — λ sweep capability (adapter side) — G18 approved
- [ ] **Acceptance**
  - Bounded sweep (configurable points, default 8) executed by the adapter that supports it, emitting λ / MFE / CAI / GC / chosen-flag points with the folding engine named (QC-2.1, QC-2.5)
  - Sweep is ORF-scoped and labelled CDS-only; no whole-mRNA claim (QC-2.1)
  - Points are carried as a design artifact so QC rendering stays pure — this split was approved 2026-11-16 (AD-4), so no execution logic enters `qc/`
  - Pre-flight time estimate available for the sweep (feeds T06)
- **Verify:** `pytest tests/unit/design/test_lambda_sweep.py -q`; `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --only lineardesign` then inspect `lambda_sweep.csv`
- **Files:** `mrna_design/adapters/lineardesign.py`, `mrna_design/design/contracts.py`, `tests/unit/design/test_lambda_sweep.py`
- **Depends:** T32, T23

### ✅ Checkpoint CP3 — `rna-design` golden
- [ ] `pytest tests/unit/design -q` and `pytest tests/integration/test_adapter_contract.py -q` green
- [ ] The default pair (`codonbert` CDS + reference UTRs) yields one design; adding `lineardesign` as an explicit second adapter yields two designs + comparison table + reconstructable `MrnaRecord`
- [ ] Every CDS retranslates to the input protein; determinism matches declarations; snapshot recorded with tolerance and reason
- [ ] `default_adapters` assertion: no GPU, no experimental; construct-source substitution surfaced
- [ ] Envelope abort demonstrated past `lineardesign`'s declared range, with the limit, estimate and alternatives (RD-5.1)
- [ ] Default 5′ and 3′UTR come from the reference library and are labelled *reference, not optimised* (RD-4.1c, RD-SC12)
- [ ] Human review of the golden outputs before QC work starts

---

## Phase 3b — `experimental-tier` (PARADE only)

> Scope added by the 2026-11-16 review (G15). PARADE is V1 in `CAPABILITY-MAP.md`; it is an **opt-in
> UTR option**, never the default and never an automatic fallback. The reliability contract in
> `SPEC-experimental-tier.md` is binding from its first implementation.

### T41A — PARADE install/pip re-pin spike, weights and licence
- [ ] **Acceptance**
  - One-session spike: install PARADE on the pinned runtime (its upstream `environment.yml` is conda-only), run one 5′ and one 3′ generation example, record wall clock / peak RAM / failure modes
  - Weight source, hash and redistribution status recorded; if weights cannot be redistributed, the fetch path is documented and the failure mode is an actionable message, never a silent checkpoint swap (XT-1.6)
  - pip re-pin plan written: PARADE is `best_effort` until it installs without conda, then `supported` (XT-2.4)
  - Licence recorded (MIT confirmed upstream), plus the upstream paper's stated scope/limitations for the caveats doc (XT-1.4, XT-1.8)
- **Verify:** spike log committed; `DECISIONS.md` records G15 outcome and the PARADE maturity label; manifest entry validates
- **Files:** `docs/spikes/parade.md`, `DECISIONS.md`, `mrna_design/tools/manifest.yaml`
- **Depends:** T23

### T41B — Experimental registry, opt-in gate and hard labelling
- [ ] **Acceptance**
  - Separate registry under `mrna_design/experimental/`; the proven registry has no reference to it (RD-2.10, import test)
  - Off by default in the notebook, in headless runs, and in every config path; enabling it is an explicit in-run action that states what it is and is not; no preset or saved profile may pre-enable it (XT-1.1, XT-1.10)
  - Labelling is generated by the framework, not per adapter: `experimental` marker, model name + pinned version, citation, upstream scope/limitations, fixed no-validation sentence (XT-1.4)
  - A disabled/unavailable experimental engine still appears in the list with the reason (RD-6.6, XT-1.7)
  - Gate tests cover notebook, headless and config paths (XT-SC1)
- **Verify:** `pytest tests/experimental/test_opt_in_gate.py tests/experimental/test_labelling.py -q`
- **Files:** `mrna_design/experimental/registry.py`, `mrna_design/experimental/labelling.py`, `tests/experimental/test_opt_in_gate.py`, `tests/experimental/test_labelling.py`
- **Depends:** T41A, T08

### T41C — PARADE adapter: 5′/3′UTR generation and prediction
- [ ] **Acceptance**
  - One module, two roles behind the plugin contract: generation (diffusion or genetic algorithm) and prediction (activity, stability) (XT-2.4)
  - Output validated structurally — nucleotide alphabet, length bounds, no accidental start codon where that would be wrong — before being offered downstream (XT-2.5)
  - Model-assigned score/rank preserved with its upstream meaning; no re-normalisation and no automatic winner (XT-2.2, XT-2.3)
  - Missing GPU/weights/dependency → `not_run` with a reason; never a silent fallback or a `pass` (XT-1.7)
  - Reproducibility gate: recorded snapshot for a fixed seed on the declared runtime, or a documented tolerance with its reason — written down before the snapshot (XT-1.5)
  - Declared runtime/ceiling aborts instead of stranding the session (XT-1.9)
- **Verify:** `pytest tests/experimental/test_parade.py -q`; `pytest -m "experimental and not gpu" -q`; `pytest -m "experimental and gpu" -q` recorded
- **Files:** `mrna_design/experimental/parade.py`, `mrna_design/experimental/weights.py`, `tests/experimental/test_parade.py`, `tests/experimental/snapshots/parade.json`
- **Depends:** T41B, T30

### ✅ Checkpoint CP3b — PARADE
- [ ] Off by default in notebook, headless and every config path; enabling is explicit and recorded (XT-SC1)
- [ ] Every artifact carries marker, pinned version, citation, caveat (XT-SC4)
- [ ] Reproducibility gate passes, or PARADE reports `not_run`/`unavailable` with a reason (XT-SC2, XT-1.7)
- [ ] No import edge from `qc` or `dna-construct` into `mrna_design/experimental/` (XT-SC6)
- [ ] `default_adapters` unchanged by PARADE's presence (RD-SC15)
- [ ] Human review of the labelling wording before the report integration in CP4

---

## Phase 4 — `rna-qc-additions`

### T42 — `CheckResult` model, threshold loader, pass labelling
- [ ] **Acceptance**
  - `CheckResult` fields exactly QC-1.2; `status` is a closed enum including `not_run`, distinct from `pass`
  - `not_run` construction requires a reason; rendering a `not_run` without one is impossible
  - All numeric thresholds/threshold ranges load from `data/thresholds/qc.yaml` with citation + effective date; no threshold literal in Python (QC-1.3)
  - Checks are pure `(record) -> CheckResult`, order-independent, no randomness (QC-1.1)
  - Each result records which invocation produced it: design-record pass vs post-assembly pass, never merged (QC-1.6)
  - Region scope is explicit per check (`mrna` / `utr5` / `cds` / `utr3`), and poly(A) is its own region excluded from density metrics (QC-1.4)
- **Verify:** `pytest tests/unit/qc/test_model.py tests/unit/qc/test_thresholds.py -q`
- **Files:** `mrna_design/qc/model.py`, `data/thresholds/qc.yaml`, `tests/unit/qc/test_model.py`, `tests/unit/qc/test_thresholds.py`
- **Depends:** T07, T29

### T42A — Delta spec: deferred additions 2/4/5 report `not_run` by decision
- [ ] **Acceptance**
  - Delta to QC-1.2/QC-3.2/QC-7.3 written and approved: a check whose threshold/library/engine is undecided emits `not_run` with a reason and a recovery hint, and the report distinguishes *not implemented* from *not selected* from *not available* (QC-1.2, QC-3.2, QC-7.3)
  - QC-SC1 restated as partial by recorded decision: additions 1, 3, 5a are complete; 2, 4, 5b are present and `not_run`; "all six pass" is not claimed
  - The delta forbids any placeholder threshold, motif or substitution that would turn `not_run` into `pass` (QC-1.3, QC-1.8)
  - `DECISIONS.md` records G10–G14 as deferred, with the user-visible reason text for each
- **Verify:** spec reviewed and `Status:` approved; `DECISIONS.md` names QC OQ1–OQ5 and QC-SC1
- **Files:** `SPEC-qc-deferred.md`, `DECISIONS.md`
- **Depends:** T42

### T43 — Motif library loader and overlap-aware scanner
- [ ] **Acceptance**
  - Library entry requires `id`, `name`, IUPAC/regex pattern, regions, severity, source (database+version or citation), notes, ≥1 positive and ≥1 negative fixture (QC-5.1)
  - Load fails on a missing fixture, missing citation, or typo'd IUPAC code (QC-5.4, QC-SC3)
  - Scanner is overlap-aware and reports every hit with coordinates and region (QC-5.3)
  - Library loading is a versioned snapshot committed to the repo; no live fetch (QC-5.1a)
  - Adding a motif is data + fixtures only — no code change (QC-5.5)
- **Verify:** `pytest tests/unit/qc/test_motif_library.py -q`; `pytest tests/unit/qc/test_motifs.py -q`
- **Files:** `mrna_design/qc/library.py`, `tests/unit/qc/test_motif_library.py`, `tests/unit/qc/test_motifs.py`
- **Depends:** T42

### T44 — Motif curation batch 1: ARE, polyadenylation, splice sites — 🔒 BLOCKED (G12, G13)
- [ ] **Note:** G12/G13 **deferred and agreed** 2026-11-16; T42A records the user-visible `not_run` reason. This task stays blocked until a release is selected and signed off; no placeholder or "remembered" motif may enter the library to unblock it.
- [ ] **Acceptance**
  - ARED-Plus-class AU-rich elements, PolyA_DB/PolyASite-class polyadenylation signals, and 5′/3′ splice-site-like motifs imported as a versioned snapshot with database name, version, retrieval date and filtering recorded (QC-5.1a, QC-5.2)
  - Splice-site scope fixed by G13: consensus scanning only, or the scoring engine is a separate gated addition
  - Every entry has positive and negative fixtures that pass
  - Excluded database classes and the reason are recorded
- **Verify:** `pytest tests/unit/qc/test_motif_library.py -q`; library load with `--strict`
- **Files:** `data/motifs/library.yaml`, `docs/motif-sources.md`, `tests/unit/qc/test_motif_batch1.py`
- **Depends:** T43

### T45 — Motif curation batch 2: G-quadruplex, Kozak-adjacent AUG, RIG-I/IFN — 🔒 BLOCKED (G12)
- [ ] **Note:** G12 **deferred and agreed** 2026-11-16 (T42A); task stays blocked. Same rule: no entry without a citation and fixtures.
- [ ] **Acceptance**
  - G4Hunter/QuadBase-class G-run entries with the database provenance recorded
  - Kozak-adjacent AUG contexts outside the intended start, with the search rule stated
  - RIG-I/IFN-associated motifs curated from primary literature with per-entry citation (no database exists — QC-5.2)
  - Optional RNA-binding-protein class either included with provenance or recorded as deferred
- **Verify:** `pytest tests/unit/qc/test_motif_batch2.py -q`; every entry resolves its citation
- **Files:** `data/motifs/library.yaml`, `docs/motif-sources.md`, `tests/unit/qc/test_motif_batch2.py`
- **Depends:** T44

### T46 — Addition 2: CpG / UpA analysis — 🔒 BLOCKED (G11)
- [ ] **Note:** G11 **deferred and agreed** 2026-11-16 (T42A). Without an approved reference panel there is no citable threshold, so this task cannot produce the `warn`/`fail` half of QC-3.2. Do not substitute a made-up percentile.
- [ ] **Acceptance**
  - Counts, density per 100 nt, longest run, per-region breakdown (5′UTR, CDS, 3′UTR, poly(A) excluded) (QC-3.1)
  - Thresholds are source-backed ranges, reference-derived where no validated cut-off exists, labelled *reference-derived, not a safety threshold* (QC-1.8, QC-3.2)
  - Reference panel, percentile and its licence recorded per G11 (QC OQ3)
  - Module measures only: no recoding, no mitigation; when `dnachisel` ran, before/after measurements and applied constraints are shown with the statement that constraint choice was the user's design decision (QC-3.3)
  - A test asserts no synonymous-recoding path exists in the module (QC-3.4)
- **Verify:** `pytest tests/unit/qc/test_cpg_upa.py -q`; known-answer fixture with exactly three CpG sites
- **Files:** `mrna_design/qc/cpg_upa.py`, `data/thresholds/cpg_upa.yaml`, `tests/unit/qc/test_cpg_upa.py`
- **Depends:** T42

### T47 — Addition 3: m1Ψ U-run and slippery-sequence analysis
- [ ] **Acceptance**
  - U homopolymer runs ≥4 reported with position, length, region and distance from CDS start (QC-4.1)
  - Slippery-heptamer class from `data/motifs/slippery.yaml` with citations; U-rich run + downstream stimulator
  - Results reported per reading-frame context; no quantitative frameshift rate implied (QC-4.2)
  - Data file records the modification context each entry is justified for; report states the analysis is assumption-based (QC-4.4)
  - Reports and warns only; mitigation documented as a `dnachisel` constraint at design time (QC-4.3)
- **Verify:** `pytest tests/unit/qc/test_m1psi.py -q`; fixture with a U-run at a known offset
- **Files:** `mrna_design/qc/m1psi.py`, `data/motifs/slippery.yaml`, `tests/unit/qc/test_m1psi.py`
- **Depends:** T42

### T48 — Addition 5a: Kozak context check
- [ ] **Acceptance**
  - Reports −6..−1 and +4 nucleotides relative to the start codon, strength class against the cited consensus table, and the deviation (QC-6.1)
  - Consensus table is data with a citation
  - When assembly inserted/substituted Kozak bases, the post-assembly pass reports the context actually ordered and each row states which pass produced it (QC-6.1, QC-1.6)
  - Check is pure and works on any contract-valid `MrnaRecord` (QC-1.7)
- **Verify:** `pytest tests/unit/qc/test_kozak.py -q`; known-answer contexts including a strong and a weak Kozak
- **Files:** `mrna_design/qc/kz_sp_tm.py`, `data/thresholds/kozak.yaml`, `tests/unit/qc/test_kozak.py`
- **Depends:** T42

### T49 — Addition 5b: signal peptide and transmembrane predictors — 🔒 BLOCKED (G5, G10)
- [ ] **Note:** G10 **deferred and agreed** 2026-11-16 (T42A) — the TM engine choice is not made, so TM can only ship as `not_run` with a reason. G5 (licences) is still open. Neither check may be rendered as `pass` to fill the gap (QC-6.3).
- [ ] **Acceptance**
  - DeepSig and PEFT-SP adapters registered under the plugin contract as predictors, selectable per step, pinned and cited in the report (QC-6.2)
  - TM engine implemented if G10 chose one; otherwise TM returns `not_run` with its own reason, never `pass`, and never shares a status or reason with signal peptide (QC-6.2a, QC-6.3)
  - Predictor confidence semantics passed through unmodified; no re-binning (QC-6.4)
  - Report links the protein-level prediction to the nucleotide design (QC-6.4)
  - Predictor-vs-user-annotation contradiction yields `warn` with both claims, never auto-resolved (QC-6.5)
- **Verify:** `pytest tests/unit/qc/test_kz_sp_tm.py -q`; injected-unavailability test asserts `not_run` + reason (QC-SC6)
- **Files:** `mrna_design/adapters/deepsig.py`, `mrna_design/adapters/peft_sp.py`, `mrna_design/adapters/tm_predictor.py`, `tests/unit/qc/test_kz_sp_tm.py`
- **Depends:** T42, T21, T30

### T50 — Addition 1: λ trade-off and cross-adapter plots — G18 approved
- [ ] **Acceptance**
  - `lambda_sweep.csv` (λ, MFE, CAI, GC, chosen) + PNG/SVG emitted from adapter-produced points; every point labelled CDS-only (QC-2.1)
  - Where no sweep exists, a cross-adapter MFE-vs-CAI plot is emitted instead of an empty figure (QC-2.2)
  - Chosen operating point marked with the printed rule `user-selected` — no knee-point heuristic (QC-2.3)
  - Legible at 100 % zoom: axis units, adapter/λ labels, caption naming the producing tool (QC-2.4)
  - Every MFE/diversity value names its folding engine; no cross-engine series or ranking (QC-2.5, RD-SC14)
- **Verify:** `pytest tests/unit/qc/test_lambda_tradeoff.py -q`; plot-data assertions + report snapshot (QC-SC7)
- **Files:** `mrna_design/qc/lambda_tradeoff.py`, `tests/unit/qc/test_lambda_tradeoff.py`, `tests/unit/qc/test_cross_adapter_plot.py`
- **Depends:** T42, T41

### T51 — Poly(A) region reporting — 🔒 BLOCKED (G14)
- [ ] **Note:** G14 **deferred and agreed** 2026-11-16 (T42A). Length and the "added enzymatically" statement are still required (QC-1.4); only the *integrity* judgement waits on G14.
- [ ] **Acceptance**
  - Poly(A) length and integrity reported separately from dinucleotide/GC/homopolymer density metrics, which exclude the tract (QC-1.4)
  - For a `pcr` template the report states no tract is encoded and the tail is added enzymatically (DC-2.2 wording alignment)
  - G14 decision applied: integrity reported separately or explicitly out of scope with the reason recorded
  - No pass/fail claim that a sequence check cannot support (QC OQ5)
- **Verify:** `pytest tests/unit/qc/test_polya.py -q`
- **Files:** `mrna_design/qc/polya.py`, `tests/unit/qc/test_polya.py`, `data/thresholds/qc.yaml`
- **Depends:** T42

### T52 — Consolidated report: HTML, `qc_summary.csv`, report CLI
- [ ] **Acceptance**
  - One self-contained HTML (no external CSS/JS/fonts) plus `qc_summary.csv`, one row per check result (QC-7.1)
  - Structure: run identity/provenance, headline warnings ordered by severity then region, per-addition sections, full result table with thresholds and citations, and a clearly labelled experimental section — empty when PARADE is off, rendering PARADE's own results when it was opted in, never merged with proven results (QC-7.2, XT-1.3)
  - PARADE values never enter `qc_summary.csv` status columns and never change run status; an isolation test proves it (XT-1.3, XT-SC3)
  - Every rendered row shows id, region, status, observed value, threshold + `threshold_ref`, citation; a row without a citation fails rendering (QC-7.3, QC-SC2)
  - No composite score, no "recommended design"; cross-candidate comparison is a table only (QC-7.4)
  - Fixed non-dismissible disclaimer (QC-7.5)
  - Byte-identical double render except the isolated run-id/timestamp header (QC-7.6, QC-SC4)
  - `python -m mrna_design.report --run <dir> --out <html>` works standalone
- **Verify:** `pytest tests/unit/report -q`; `python -m mrna_design.report --run outputs/<run_id> --out /tmp/report.html`
- **Files:** `mrna_design/report/render.py`, `mrna_design/report/templates/qc.html.j2`, `mrna_design/report/__main__.py`, `tests/unit/report/test_render.py`, `tests/unit/report/test_determinism.py`
- **Depends:** T42, T46, T47, T48, T50, T51

### T53 — Post-assembly QC edge (two-pass reporting)
- [ ] **Acceptance**
  - `run.py` invokes the same check set on the design record and, when assembly ran, on the assembled mRNA (QC-1.6, QC-1.7)
  - The report labels each result's invocation and never merges the two into one status
  - When assembly did not run, only the design-record pass is reported and the gap is stated
  - `dna-construct` imports no QC module; the edge exists only in the composition root (import test)
- **Verify:** `pytest tests/integration/test_qc_two_pass.py -q`; import-boundary test still green
- **Files:** `mrna_design/run.py`, `tests/integration/test_qc_two_pass.py`
- **Depends:** T52

### ✅ Checkpoint CP4 — QC
- [ ] `pytest tests/unit/qc -q` and `pytest tests/unit/qc/test_motif_library.py -q` green
- [ ] `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --qc-only` emits CSV + one self-contained HTML
- [ ] Double render byte-identical; every row cited; `not_run` rows carry reasons; no composite score
- [ ] Cross-adapter run of the same check suite passes (QC-SC5)
- [ ] With PARADE opted in, its results render in the experimental section only and touch no `qc_summary.csv` status column (XT-1.3, XT-SC3)
- [ ] With PARADE off, the section is present and empty, and no proven-path `not_run` is attributable to it
- [ ] Human review of the report wording before construct work starts

---

## Phase 5 — `dna-construct`

### T54 — RNA→DNA conversion and construct input validation
- [ ] **Acceptance**
  - Accepts a `DesignResult`, a carried-forward export, or a user-supplied sequence with no design step run (DC-1.1, NS-2.5)
  - Accepts mRNA (U) or DNA (T); DNA is the coding strand; conversion applied exactly once and recorded in manifest and summary; mixed T/U rejected with positions (DC-1.2)
  - Validates single sequence, legal nucleotides, CDS in frame, start/stop present, no internal stops; failures name region and coordinate (DC-1.3)
  - Multi-insert/polycistronic rejected pointing at the deferred item (DC-1.4)
  - One-codon ORF accepted with warning; zero codons or non-multiple-of-three rejected; no padding (DC-1.5, DC-SC12)
- **Verify:** `pytest tests/unit/construct -q`; boundary tests for 1 codon and a 2-nt insert
- **Files:** `mrna_design/construct/rna_to_dna.py`, `tests/unit/construct/test_rna_to_dna.py`, `docs/construct-formats.md`
- **Depends:** T07, T28

### T55 — Linear IVT template assembly, junctions, Kozak, T7, poly(A) rules
- [ ] **Acceptance**
  - Domain chain asserted in order: 5′UTR → Kozak (optional) → signal peptide (optional) → antigen → 3′UTR → poly(A) only when the template encodes it (DC-2.1); out-of-order domain is a hard failure
  - Template type drives poly(A), and poly(A) is never optimised (G22 resolved): `pcr` carries none and says the tail is added enzymatically; `plasmid` encodes a user-set length (default 100 nt) with a homopolymer warning (DC-2.2); no poly(A) control or toggle exists anywhere (DC-SC10)
  - Kozak insertion is opt-in, cited from `data/`, every altered base listed in the junction map, and a recorded warning names the upstream decision it discarded (DC-2.3)
  - Signal peptide is annotation only, using the declared span; nothing is reverse-translated (DC-2.4)
  - Promoter path follows template type: `pcr` with empty `five_prime_flank` prepends exactly one cited T7 block; a supplied flank replaces it, never stacks (DC-2.5, DC-SC13)
  - Summary prints template type, total and per-region lengths, GC%, poly(A) status, SP span, promoter source, and a 5′→3′ feature list (DC-2.6)
- **Verify:** `pytest tests/unit/construct/test_linear.py -q`; junction map reconstructs the assembled sequence
- **Files:** `mrna_design/construct/linear.py`, `data/kozak.yaml`, `data/promoters.yaml`, `tests/unit/construct/test_linear.py`
- **Depends:** T54

### T56 — Construct-level assertions
- [ ] **Acceptance**
  - One assertion module covers promoter presence/orientation/TSS, insert orientation, reading frame, poly(A) placement, and run-off linearisation site uniqueness 3′ of the poly(A) cassette for plasmids (DC-2.5, DC-3.4, DC-3.6)
  - Assertion failures are `ConstructError` with region/coordinate and block export (DC-4.4)
  - No default or bundled backbone can enter a construct; absence resolves to `pcr` (DC-3.0, DC-SC9)
  - Cloning feasibility is explicitly not evaluated; the assertion set says so (DC-3.7)
- **Verify:** `pytest tests/unit/construct/test_checks.py -q`; negative cases for reverse orientation and frame mismatch
- **Files:** `mrna_design/construct/checks.py`, `tests/unit/construct/test_checks.py`
- **Depends:** T55

### T57 — GenBank/FASTA emission and mandatory round-trip
- [ ] **Acceptance**
  - `construct.gb` + `construct.fasta` emitted with annotated features: promoter, UTRs, CDS, signal peptide, poly(A), insertion boundaries (DC-5.1, DC-5.3)
  - Re-parsing yields identical sequence, identical feature set, and a CDS that translates to the original protein (DC-5.2, DC-SC2)
  - Provenance links the source design (adapter, tool version, seed) and backbone hash (DC-5.4)
  - Golden construct snapshots cover the feature table and summary text, not the binary image
- **Verify:** `pytest tests/integration/test_construct_roundtrip.py -q`
- **Files:** `mrna_design/construct/emit.py`, `tests/integration/test_construct_roundtrip.py`, `tests/fixtures/golden_rbd/construct_expected/feature_table.tsv`
- **Depends:** T55, T56

### T58 — Circular plasmid: parse, validate, insert, remap features
- [ ] **Acceptance**
  - Backbone accepted as GenBank/FASTA path first, upload widget as convenience (NS-1.6); parsed with Biopython; single circular record, parseable features; feature list echoed for user confirmation (DC-3.1)
  - No bundled backbones; manifest records file hash and parsed feature list (DC-3.2)
  - Insertion by explicit coordinates or a chosen site pair; deterministic splicing; diff against input shows exactly one contiguous replaced span (DC-3.3, DC-SC3)
  - Orientation and frame asserted, mismatch is a hard failure (DC-3.4)
  - Features preserved with recomputed coordinates; ambiguous mappings reported; origin-crossing and insertion-spanning features handled (DC-3.5, DC-SC4)
- **Verify:** `pytest tests/unit/construct/test_plasmid.py tests/unit/construct/test_feature_remap.py -q`; origin-wrap and insertion-span negative tests
- **Files:** `mrna_design/construct/plasmid.py`, `tests/unit/construct/test_plasmid.py`, `tests/unit/construct/test_feature_remap.py`
- **Depends:** T55, T56

### T59 — Restriction-site analysis via Biopython tables
- [ ] **Acceptance**
  - Uses Biopython's `Restriction` tables; no hand-written recognition-site list (DC-3.6)
  - Reports unique sites suitable for linearisation, internal sites for the chosen enzyme, and site counts in insert vs backbone
  - For plasmids, asserts the run-off site is 3′ of the poly(A) cassette and unique
  - Report states cloning/ligation compatibility was not simulated (DC-3.7, DC-SC6)
- **Verify:** `pytest tests/unit/construct/test_restriction.py -q`; duplicate-site negative case
- **Files:** `mrna_design/construct/restriction.py`, `tests/unit/construct/test_restriction.py`
- **Depends:** T56

### T60 — Gene-synthesis order block and generic profile validation — 🔒 BLOCKED (G9)
- [ ] **Acceptance**
  - `order_block.csv` with the vendor-neutral schema and exactly one profile in V1 (DC-4.1, DC-4.2)
  - `kind` accepts `gene_fragment` and `oligo`; V1 emits `gene_fragment` only
  - Per-row validation: hard failures block export, synthesis risks warn in CSV and summary (DC-4.3)
  - Export blocked when any construct assertion failed, listing every violation (DC-4.4, DC-SC5)
  - Fixed note: convenience export, must be checked in the vendor's tool, not a validated order (DC-4.5)
  - Profile rules resolve to source + check date or `unspecified`; stale rules warn (DC-SC11)
- **Verify:** `pytest tests/unit/construct/test_order.py -q`; re-parse CSV against the profile schema
- **Files:** `mrna_design/construct/order.py`, `data/vendors/generic.yaml`, `tests/unit/construct/test_order.py`
- **Depends:** T57; **G9 resolved**

### T61 — Construct map rendering — 🔒 BLOCKED (G16)
- [ ] **Acceptance**
  - Map rendered through the pinned plotting library's API with features passed in; no hand-rolled coordinate transforms (DC-5.3)
  - Labels identify promoter, UTRs, CDS, poly(A), backbone features, insertion boundaries; legible at report zoom
  - PNG + SVG emitted; rendering is deterministic for identical input
  - G16's chosen library is recorded as a dependency decision and pinned
- **Verify:** `pytest tests/unit/construct/test_map.py -q`; open both files and check labels
- **Files:** `mrna_design/construct/map.py`, `tests/unit/construct/test_map.py`
- **Depends:** T57, T58; **G16 resolved**

### T62 — Construct summary and provenance
- [ ] **Acceptance**
  - `construct_summary.md` contains junctions, checks, provenance, caveats (DC-5.1)
  - Summary states template type, per-region lengths, GC%, poly(A) status, SP span, promoter source, feature list (DC-2.6)
  - Summary states cloning feasibility was not simulated (DC-SC6)
  - When the source design contains a PARADE (experimental) region, the construct and order block are flagged `experimental_derived` in filename metadata, summary and CSV notes, and using it required an explicit confirmation in that run (DC-5.5, XT-1.2)
- **Verify:** `pytest tests/unit/construct/test_summary.py -q`; snapshot assertion on required sentences
- **Files:** `mrna_design/construct/summary.py`, `tests/unit/construct/test_summary.py`
- **Depends:** T57, T59

### T63 — Construct-only run path
- [ ] **Acceptance**
  - `run_modules=["construct"]` with a pasted mRNA or DNA sequence produces a complete construct + CSV bundle with design recorded `not run` with reason (DC-SC14, NS-SC9)
  - Sequence source recorded as `user` or `run:<previous_run_id>` (NS-2.5)
  - Selling point: a user with a sequence from elsewhere can skip Module 1 entirely
  - No design import is exercised and the cache is not consulted
- **Verify:** `pytest tests/integration/test_construct_only.py -q`; inspect manifest statuses
- **Files:** `mrna_design/run.py`, `tests/integration/test_construct_only.py`
- **Depends:** T54, T57, T60

### ✅ Checkpoint CP5 — Construct
- [ ] `pytest tests/unit/construct -q` and `pytest tests/integration/test_construct_roundtrip.py -q` green
- [ ] Default path (no backbone) emits linear template + order block with zero errors and a `backbone_path` hint (DC-SC8)
- [ ] Backbone path round-trips; diff exactly one span; feature edge cases handled or reported
- [ ] Blocked export lists every violation; summary says cloning was not simulated
- [ ] With a PARADE-derived UTR, construct and order CSV carry `experimental_derived` (XT-1.2, DC-5.5)
- [ ] Human review of one linear and one plasmid construct before release work

---

## Phase 6 — Integration and release

### T64 — Golden default-path end-to-end
- [ ] **Acceptance**
  - One command on the golden fixture produces: optimised mRNA, consolidated QC report, linear IVT template, order block, and a downloadable bundle — with only the sequence supplied (CAPABILITY-MAP §V1 definition of done)
  - Bundle assertion covers the union of NS-4.1, RD-4.2, QC-7.1, DC-5.1 file sets
  - Default path is CPU-only, contains no GPU and no experimental adapter, and no step asks a question (NS-SC1, NS-SC7, RD-SC9); the manifest records the experimental toggle as off by default (XT-1.1)
  - Post-assembly QC results appear and are labelled distinctly from the design-record pass
- **Verify:** `pytest -m e2e -q`; `python -m mrna_design.run --config tests/fixtures/golden_rbd.yaml --out /tmp/run`
- **Files:** `tests/e2e/test_golden_default_path.py`, `tests/e2e/test_bundle_contract.py`, `docs/run-bundle.md`
- **Depends:** CP3, CP4, CP5

### T65 — Multi-adapter golden run with report and comparison snapshots
- [ ] **Acceptance**
  - Two or more CDS engines on the golden protein produce a comparable table with no missing common metrics (RD-SC3)
  - The same QC suite runs over every adapter's result unchanged (QC-SC5)
  - Two folding engines keep MFE series separate in report and manifest (RD-SC14)
  - Report snapshot stable with timestamps normalised
- **Verify:** `pytest -m "network and not gpu" -q`; report snapshot diff empty
- **Files:** `tests/e2e/test_golden_multi_adapter.py`, `tests/fixtures/golden_rbd.yaml`, `tests/fixtures/golden_rbd/snapshots/report.html`
- **Depends:** T64

### T66 — Manifest freshness CI job
- [ ] **Acceptance**
  - Scheduled job resolves every pinned revision, refreshes `last_verified`, fails on unreachable entry or age > `stale_after_days` (NS-3.7)
  - Job writes a machine-readable report; failures name the entry and the reason
  - A backdated entry demonstrably fails the check (unit test with injected clock)
- **Verify:** `pytest tests/unit/tools/test_freshness.py -q`; manual `workflow_dispatch` run of the scheduled job
- **Files:** `.github/workflows/manifest-freshness.yml`, `mrna_design/tools/verify.py`, `tests/unit/tools/test_freshness.py`
- **Depends:** T12, CP2

### T67 — Release documentation set
- [ ] **Acceptance**
  - `README.md`: what it does, one-notebook promise, the licence-responsibility model (research **and** commercial use; per-engine terms disclosed — default `codonbert` per G2's weights verdict; restricted engines — `lineardesign` included — say "contact the rights holder" and never promise a licence; `custom` is GPL-3.0 in its separate `mrna-design-custom` package), and how to switch engines (NS-3.8 delta, `mRNADesign.md` §Licensing, G25/G26 resolutions, §Licence wording rule)
  - `docs/metrics.md`, `docs/qc-checks.md`, `docs/construct-formats.md`, `docs/fixtures.md`, `docs/re-pin.md`, `docs/known-limitations.md`, `docs/outputs-layout.md` complete and consistent with code
  - `docs/experimental-caveats.md` holds PARADE's training scope, what it predicts, known failure modes, and when its output should be ignored — cited from the report (XT-1.8)
  - `THIRD-PARTY-NOTICES.md` matches `tools/manifest.yaml` exactly (generated or validated by a test), and the README states which dependencies are research-only
  - No document claims clinical, regulatory or wet-lab validation
  - `DECISIONS.md` contains every gate resolution and every spec delta
- **Verify:** link check on docs; grep for forbidden claims ("validated", "safe", "approved") in user-facing text
- **Files:** `README.md`, `docs/metrics.md`, `docs/qc-checks.md`, `docs/known-limitations.md`, `docs/experimental-caveats.md`
- **Depends:** CP5

### T68 — Quality gate and Colab manual release check
- [ ] **Acceptance**
  - `ruff check . && ruff format --check .` and `mypy mrna_design` clean
  - `pytest --cov=mrna_design --cov-report=term-missing --cov-fail-under=80` green with module minimums (contracts/adapters 95, qc 85, construct 85, tools/ledger near-total)
  - `pytest -m network`, `pytest -m gpu`, `pytest -m e2e` results recorded per runtime, including GPU-absent outcomes
  - Manual Colab CPU check on a fresh session: only the sequence entered, Run all, full bundle, no dialog, no traceback (NS-SC1, NS-SC7)
  - Notebook smoke green on the pinned runtime (NS-SC6, DC-SC8)
- **Verify:** the Command block from `SPEC-notebook-shell.md` §Commands, plus the manual checklist in `docs/release-checklist.md`
- **Files:** `pyproject.toml`, `.github/workflows/ci.yml`, `docs/release-checklist.md`
- **Depends:** T64, T65, T66, T67

### T69 — Release, and only now: version control starts
- [ ] **Acceptance**
  - **V1 is complete before this point** (item 7): `git init`, the first commit, `LICENSE` (MIT, holder filled in by you) and `THIRD-PARTY-NOTICES.md` (generated from `tools/manifest.yaml`) are created here, not earlier
  - `.gitignore` written at this point, not before; repository layout is proposed as part of this task and approved by you first
  - The public licence claims drafted in `docs/licence-claims.md` are published in `README.md`; the dependency classes (including any `copyleft` or `research_only`) are stated with the exact consequence
  - `CHANGELOG.md` records V1 scope, and the V1 definition of done is traceable to the CP6 evidence
  - Tag + GitHub release with the notebook link; no wheel/sdist promised to end users (Colab-only)
  - `DECISIONS.md` records what shipped differently from the plan and why
  - Known limitations and every deferred item are listed in the release notes
  - G15's PARADE outcome and the follow-on unit for `experimental-tier` are recorded so V2 does not re-litigate
- **Verify:** release page renders; `CHANGELOG.md` covers every phase; tag exists
- **Files:** `.gitignore`, `LICENSE`, `THIRD-PARTY-NOTICES.md`, `CHANGELOG.md`, `DECISIONS.md`, `docs/release-checklist.md`
- **Depends:** T68

### ✅ Checkpoint CP6 — Release
- [ ] All CP0–CP5 checkpoints re-run green on the release candidate
- [ ] All spec success criteria traced to evidence (plan §Traceability)
- [ ] Every skip, `not_run`, and exclusion visible in the golden bundle
- [ ] Human sign-off on the research-only claim and the licence map

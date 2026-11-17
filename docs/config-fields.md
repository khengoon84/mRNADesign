# Configuration fields — approved taxonomy (T05)

**Status:** implemented 2026-11-17. The three-class taxonomy is **approved**
(`tasks/plan.md` §Decision record #3, G19/G20; `tasks/todo.md` T05). The source
of truth is `mrna_design/config.py`; `tests/unit/test_config_schema.py`
asserts every field below against the schema, including a drift test that this
table and `RunConfig.field_specs()` name exactly the same fields and classes.

The taxonomy exists because "optional field with a default" hides two different
acts: supplying material that changes what a user would order, and choosing a
convention that merely formats the output. `SPEC-notebook-shell.md` NS-1.2a
defines the classes; NS-2.1 makes one validated `RunConfig` the only pipeline
input; NS-2.2 fixes the error surface; NS-2.3 forbids hidden defaults.

## Class definitions

| Class | Meaning | Default rule |
|---|---|---|
| `required` | The sequence input the run cannot start without. The requirement is conditional on `run_modules` (G20). | No value; supply one of the two sequence fields for the mode. |
| `material` | A choice that changes what a user would order. | **No value default, ever.** Absent resolves to a declared skip with a recovery hint (NS-5.4, DC-3.0). |
| `representation` | A convention or formatting choice with a declared, written-out default. | A declared default may exist; resolution writes it explicitly into `config.resolved.yaml` (NS-2.3). |

## Field table

| Field | Class | Type | Declared default | Rule and requirement |
|---|---|---|---|---|
| `protein_sequence` | `required` | `str \| null` | `null` | Required when `run_modules` includes `design`; whitespace-only is rejected (NS-1.2, NS-1.7, G20, RD-1.1). Normalisation and hashing belong to `rna-design` (RD-1.4). |
| `sequence_input` | `required` | `str \| null` | `null` | Required when `run_modules` excludes `design`, so Module 2 runs with no protein and no design step (NS-1.7, DC-1.1). |
| `backbone_path` | `material` | `str \| null` | **none — never defaulted** | The only material field. Absent means the plasmid branch is `skipped` with a recovery hint naming this field; no backbone is bundled, generated or guessed (NS-1.2a, DC-3.0, DC-3.2). A supplied path with `template_type='pcr'` is a field error, not a silent no-op. |
| `run_modules` | `representation` | `list["design" \| "construct"]` | `["design", "construct"]` | Modules to execute, each at most once, at least one (NS-1.7). |
| `template_type` | `representation` | `"pcr" \| "plasmid"` | `"pcr"` | Template vocabulary and default from DC-2.0. `plasmid` is reachable only when `backbone_path` is supplied (DC-3.0). |
| `poly_a_length` | `representation` | `int > 0 \| null` | `null` (resolved to 100 nt for `plasmid` at T06) | Poly(A) is derived from template type, never an independent toggle. `pcr` carries no tract and must leave this unset; `plasmid` uses the default 100 nt (DC-2.2). |
| `construct_source` | `representation` | `str \| null` | `"codonbert"` | A named adapter over results this run produced — not "the first result" and never a ranking; substitution is surfaced (RD-4.1b delta, G25-B). The fixture's explicit `null` is the T40 placeholder, never a runtime choice. |
| `default_adapters` | `representation` | `list[str] \| null` | `null` | Per-step default adapter set, encoded at T40 (RD-4.1a). `null` means *not encoded yet*, never *run nothing*. |
| `seed` | `representation` | `int` | `42` | One global seed, overridable per adapter; every resolved seed is recorded (RD-3.6). The value is a declared convention, not a biological parameter. |
| `adapter_seeds` | `representation` | `dict[str, int]` | `{}` | Per-adapter seed overrides keyed by adapter id (RD-3.6). Empty ids are rejected. |
| `report_title` | `representation` | `str` | `"mRNADesign run report"` | Report wording. The research-use caveat is mandated separately and is not configurable here (NS-4.3). |
| `run_label` | `representation` | `str \| null` | `null` | Optional filename-safe label for output naming; absent uses the ledger-generated run id (NS-4.1, T09). Path separators are rejected. |

## Requiredness is conditional (G20)

`protein_sequence` is required exactly when `run_modules` contains `design`;
`sequence_input` is required when it does not. A Module-2-only run is therefore
first-class and must produce a complete bundle with design recorded `not run`
with its reason (NS-1.7, NS-SC9). Validation reports a missing sequence as a
field-level message naming the field and the rule — never as a traceback.

## Material means no invented value (G19, NS-1.2a)

`backbone_path` is the only material field. It has **no value default**: an
absent path is `None`, resolution records "not supplied", and the plasmid branch
is `skipped` with a recovery hint. The schema refuses the two states that could
turn a guess into an order:

- `template_type='plasmid'` with no backbone — no bundled vector is available
  and none is invented (DC-3.0);
- a supplied `backbone_path` with `template_type='pcr'` — a material input is
  never ignored silently.

`construct_source` was named as material in the unapproved NS-1.2a text. The
approved taxonomy treats it as representation: it selects one of *this run's
results* by adapter id, carries the declared default `codonbert` (G25-B), and
falls back with a visible substitution (RD-4.1b delta). It cannot introduce
material the user did not supply.

## Representation defaults are declared, not hidden (NS-2.3)

Every representation default lives in `mrna_design/config.py` next to its
description and is visible through `RunConfig.model_fields`,
`RunConfig.field_specs()` and `model_dump()`. Resolution (T06) writes every
value — including resolved seeds and the plasmid poly(A) default — into
`config.resolved.yaml`, so the manifest can enumerate what affected the output
without a second hand-written list. A field added without a taxonomy class makes
`field_specs()` fail closed; unknown keys are rejected by `extra="forbid"`
instead of disappearing from the record.

## Validation surface (NS-2.2)

`parse_config(data)` returns a `RunConfig` or raises `ConfigValidationError`
whose `.messages` is a tuple of field-level strings (`"field.path: reason"`).
The notebook and headless runner render those messages; pydantic's
`ValidationError`, its type names and the traceback never reach the user. The
full exception chain is retained for `run.log` diagnostics at T10 (NS-5.2).

## Delta note for `SPEC-notebook-shell.md` (NS-1.2/NS-1.2a)

**Approved 2026-11-16 (G19/G20); recorded here and in the spec so code and text
cannot disagree.** The required class is conditional rather than "the protein
sequence" alone: `protein_sequence` is required exactly when `run_modules`
includes `design`, and `sequence_input` is required when it does not, so a
Module-2-only run is valid with no protein and no design step is attempted
(NS-1.7, DC-1.1). The material class contains only `backbone_path`, which has no
value default and whose absence resolves the plasmid branch to `skipped` with a
recovery hint, while `construct_source` moves to the representation class as a
named selection over results this run produced, with a declared default
(`codonbert` after G25-B) and a surfaced substitution rather than an invented
material input (RD-4.1b delta). `template_type` remains representation with the
declared default `pcr`, and `template_type='plasmid'` is reachable only when a
backbone is supplied (DC-2.0, DC-3.0).

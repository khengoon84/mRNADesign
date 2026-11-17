# Public licence claims — drafted for T69

**Status: unpublished draft, 2026-11-17 (T03).** Nothing in this file is a public claim yet.
`README.md` remains a stub and states no licence beyond pointing at the decision record. T69 publishes
these claims with the `LICENSE` file and the generated `THIRD-PARTY-NOTICES.md`, after V1 is complete
(`DECISIONS.md` D-013, D-016, D-021, D-022).

Each claim below is written to be copied into the README (or kept here with a pointer) without
strengthening it. The source column is the authority; a claim that cannot point at one is deleted, not
softened.

---

## 1. This repository's code is MIT

> The code in this repository is released under the MIT licence. The copyright holder line is filled in
> when the repository is published. The MIT grant covers this repository's own code only — not the
> upstream tools it orchestrates, not model weights, and not reference sequence data.

Source: `DECISIONS.md` D-013; `mRNADesign.md` §Licensing; MIT text at T69.

At T69: write `LICENSE` as `Copyright (c) 2026 <holder>` with the holder supplied by the owner. Until
then no `LICENSE` file exists. Do not describe the project as "MIT-licensed" in a distributable
artefact before that file is written.

## 2. The tool is built for research and commercial use, with the limitation attached to the engine

> mRNADesign is built for research **and** commercial use. Its own code is MIT. The only commercial
> limitation is the one attached to the engines you choose: a run's commercial usability is determined
> by the engines and data that produced its regions, and those terms are disclosed per engine in the
> run bundle and in the third-party notices.

Source: `mRNADesign.md` §Licensing; plan §Licence wording rule; D-017 (G25-B) and D-019.

What this does **not** say: that every engine is commercially usable, that a commercially clean default
path exists today, or that the project has cleared any dependency's terms for the user's purpose.

## 3. The default CDS engine (`codonbert`) — subject to G2

> The default CDS engine is CodonBERT. Its code is MIT; its model weights are a separate component with
> their own terms. [T69 inserts the G2 outcome here.]

Two variants are prepared. **T69 must publish exactly one, whichever G2 supports, and must not publish
this section before G2 is recorded.**

- **If G2 clears the weights for the stated use:**
  > The pinned weights are used under the terms recorded in `THIRD-PARTY-NOTICES.md`. Review those
  > terms for your own intended use.

- **If G2 does not clear the weights, or leaves the question open:**
  > The weights' terms have not been cleared for commercial use by this project.
  > Commercial use of this engine's output is not granted by this project. Contact the rights holder
  > before using the output commercially.

Either way, the README must not state or imply that the default path is commercially clean while G2 is
open. In particular: no "commercially usable by default", no "no licence needed for the default", no
"MIT end to end" — the weights are not MIT by assumption.

Source: D-017's open consequence; `SPEC-rna-design.md` RD-2.4; T18, T36, T40.

## 4. Restricted engines are the user's responsibility (`lineardesign`)

> Engines with restricted terms are explicit selections, never the default. If you select one and
> commercialise its output, any licensing obligation is yours; this project does not grant that right
> and does not promise that a licence is available. Commercial use of this engine's output is not
> granted by this project. Contact the rights holder before using the output commercially.

Source: D-019; plan §Licence wording rule; D-017 (G26: engine-selective printed notice, no click
gate); `SPEC-rna-design.md` RD-2.4, RD-2.7.

`lineardesign` is the V1 engine this applies to. The wording is uniform: the project never writes
"licence available", "can be obtained", a fee, a term, or a vendor stated as certain. Restricted
engines say "contact the rights holder" — that is the whole claim.

## 5. `custom` is GPL-3.0, in a separate package

> The CUSTOM adapter is not part of the MIT core. It ships as the separate package
> `mrna-design-custom`, licensed GPL-3.0. Installing it brings GPL-3.0 obligations: a distributed
> combination that includes it must be GPL-3.0. The core never imports it and lists it as unavailable
> until you install the package.

Source: D-018; plan §CUSTOM adapter boundary; `docs/tool-licences.md` §Copyleft.

This claim must not describe `custom` as "available with a notice". The licence of the distributed
combination changes; the notice does not fix it.

## 6. Structure-metric engines carry conditions, not a research-only restriction

> ViennaRNA and LinearFold permit research, educational and commercial use under their own conditions,
> including credit/citation. This project fetches the pinned upstream tools at run time rather than
> redistributing them, honours the credit and citation conditions in its notices and report, and does
> not embed either engine in a commercial product. If you embed one in a product, its conditions —
> including, for ViennaRNA, contacting the authors — are yours to meet.

Source: D-017 (G27, answered from source 2026-11-16); `docs/tool-licences.md` rows `viennarna-qc` and
`linearfold`.

This claim must not call the folding engines "MIT", "permissive", "GPL" or "research-only". None of
those is their class.

## 7. Reference UTR sequences are data with their own caveat

> The default 5′ and 3′UTRs are reference sequences from published vaccine designs, labelled
> *reference, not optimised*. Each carries its primary-source citation. They may be covered by patent
> claims; this project's MIT grant does not extend to them. Confirm their suitability and freedom to
> operate for your application.

Source: `mRNADesign.md` §Scope decisions; D-014; RD-4.1c; T24.

This claim must not say the sequences are "free to use", "patent-free", "licensed for commercial use",
or that they reproduce a licensed product.

## 8. No clinical, regulatory or wet-lab validation

> No clinical, regulatory or wet-lab validation is claimed for anything this notebook produces.
> Outputs are computational designs for research use. Safety, efficacy, immunogenicity, manufacturability
> and regulatory acceptability are not established here and must be assessed by you and your
> institution.

Source: `mRNADesign.md` §Licensing, §Out of scope; T67.

Do not write "validated", "safe" or "approved" as a description of the tool or its output, in any
tense and any grammatical position except a negation.

## 9. No promise that a licence exists

> Where a dependency's terms restrict commercial use, this project says "contact the rights holder". It
> does not promise that a licence exists, that one can be obtained, or on what terms.

Source: D-019; plan §Licence wording rule.

This is a claim about the project's own restraint; it is the sentence that keeps claims 3–6 honest.

---

## Claims that must not be published (T69 review list)

| Forbidden claim | Why | Replacement |
|---|---|---|
| "MIT-licensed project" before `LICENSE` exists | No licence file until T69 | State the decision and the pointer only |
| "The default path is commercially usable" | G2 open; weights unresolved | Claim 3, variant B |
| "A commercial licence is available / can be obtained" | D-019 forbids it; the project cannot verify it | "contact the rights holder" |
| "ViennaRNA is GPL / non-commercial" | Factually wrong (G27) | Claim 6 |
| "The UTRs are patent-free / free to use" | Patent status unverified | Claim 7 |
| "Validated / safe / approved" as a description | No clinical, regulatory or wet-lab evidence | Claim 8 |
| "The whole pipeline is MIT" | Upstream tools, weights and data are not | Claims 1–7 |

## Review against `mRNADesign.md` §Licensing

| Intent line | What this draft says | Status |
|---|---|---|
| The project's own code is MIT; the research restriction sits on the dependency | Claim 1, Claim 2 | Consistent |
| LinearDesign is research use only; commercial use requires the user to act | Claim 4, with the D-019 sentence instead of a promise | Consistent, worded per D-019 |
| "Because it is the default CDS engine, the default path is research-only" | **Superseded**: `codonbert` is the default after G25-B (D-017). Claim 3 records the G2 dependency instead | Stale intent line, not copied (D-022) |
| Other engines are permissive where stated and otherwise verified before pinning | Claims 5–6 and the `unverified` rows in `docs/tool-licences.md` | Consistent; no row is called permissive without a licence |
| No clinical or wet-lab validation is claimed anywhere | Claim 8 | Consistent |

No claim above exceeds `mRNADesign.md` §Licensing as amended by D-017. The draft claims less than the
intent document in two places — the default's commercial status and the LinearDesign licence path —
because the gates that would support more are open.

## Publication checklist (T69)

- [ ] Holder line supplied and `LICENSE` written; Claim 1 final
- [ ] G2 verdict recorded; exactly one variant of Claim 3 published
- [ ] `THIRD-PARTY-NOTICES.md` generated from `mrna_design/tools/manifest.yaml`; every row in
      `docs/tool-licences.md` has its notice line
- [ ] `grep -ni` for "licence available", "can be obtained", "may be available", "patent-free",
      "commercially clean" returns nothing
- [ ] `grep -ni` for "validated", "safe", "approved" returns only negations or technical
      contract language ("validated result" is not a product claim)
- [ ] The published README contains no claim absent from this file
- [ ] No claim of clinical, regulatory or wet-lab validation

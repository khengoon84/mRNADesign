"""T04: golden fixtures are cited, immutable and internally consistent.

The hashes are asserted against `docs/fixtures.md`; the protein in the config
fixture is asserted against the frozen FASTA, so the duplication cannot drift.
Changing a frozen fixture requires a new entry in `docs/fixtures.md` and a
recorded decision (SPEC-rna-design.md §Boundaries of autonomy).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "fixtures.md"
GOLDEN = ROOT / "tests" / "fixtures" / "golden_rbd"
PROTEIN = GOLDEN / "protein.fasta"
CONFIG = ROOT / "tests" / "fixtures" / "golden_rbd.yaml"
BACKBONE = ROOT / "tests" / "fixtures" / "backbones" / "puc19.gb"

# "| `tests/fixtures/...` | `64 hex chars` |"
HASH_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|\s*$")
STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")


def _documented_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for line in DOCS.read_text(encoding="utf-8").splitlines():
        match = HASH_ROW.match(line)
        if match:
            hashes[match.group(1)] = match.group(2)
    return hashes


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fasta_sequence(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith(">"), f"{path.name}: first line is not a FASTA header"
    return "".join(line.strip() for line in lines[1:] if line.strip())


def test_every_frozen_fixture_matches_its_documented_hash() -> None:
    documented = _documented_hashes()
    assert set(documented) == {
        "tests/fixtures/golden_rbd/protein.fasta",
        "tests/fixtures/backbones/puc19.gb",
    }, "docs/fixtures.md must document exactly the frozen fixture files"
    for relative_path, digest in documented.items():
        actual = _sha256(ROOT / relative_path)
        assert actual == digest, f"{relative_path} does not match docs/fixtures.md"


def test_protein_fasta_is_one_standard_record() -> None:
    sequence = _fasta_sequence(PROTEIN)
    assert len(sequence) == 223
    assert set(sequence) <= STANDARD_AA, "non-standard residue in the golden protein"
    assert sequence.startswith("RVQPTESIVR")
    assert sequence.endswith("NKCVNF")


def test_config_fixture_is_shaped_like_the_approved_taxonomy() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    config = yaml.safe_load(text)

    assert config["run_modules"] == ["design", "construct"]
    assert config["template_type"] == "pcr"
    # Material fields carry no invented value (NS-1.2a).
    assert config["backbone_path"] is None
    # Placeholders, not decisions: T40 encodes the real set.
    assert config["default_adapters"] is None
    assert config["construct_source"] is None
    # The fixture names its frozen source file (docs/fixtures.md holds the hash).
    assert "tests/fixtures/golden_rbd/protein.fasta" in text


def test_config_protein_matches_the_frozen_fasta() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["protein_sequence"] == _fasta_sequence(PROTEIN)


def test_backbone_record_is_the_documented_accession() -> None:
    record = BACKBONE.read_text(encoding="utf-8")
    assert "VERSION     M77789.2" in record
    assert "2686 bp" in record
    origin = record.split("ORIGIN", 1)[1].split("//", 1)[0]
    bases = re.sub(r"[^ACGTNacgtn]", "", origin)
    assert len(bases) == 2686


def test_v1_ships_no_runtime_backbones() -> None:
    entries = sorted(path.name for path in (ROOT / "data" / "backbones").iterdir())
    assert entries == ["README.md"], "DC-3.2: data/backbones must contain no bundled sequence files"

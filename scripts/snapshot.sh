#!/usr/bin/env bash
# Dated snapshot of the mRNADesign working tree.
#
# There is no git repository yet (DECISIONS.md D-011, D-016). This script is the
# substitute: an immutable, dated archive plus a checksum, so a bad edit is
# recoverable without committing to a repository layout prematurely.
#
# Archives are stored in backups/ inside the workspace. Copying them
# off-machine is NOT required by decision (D-020, 2026-11-17); the resulting
# risk — the archives do not survive disk failure or deletion of the
# workspace — is recorded and accepted there.
#
# Usage:
#   scripts/snapshot.sh                 # snapshot, label "manual"
#   scripts/snapshot.sh pre-phase2      # snapshot with a label
#   scripts/snapshot.sh --list          # list existing snapshots
#
# Output: backups/mrnadesign-<UTC timestamp>-<label>.tar.gz
#         backups/<same name>.README.txt
#         backups/SHA256SUMS        (append-only)

set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SNAP_DIR="$ROOT/backups"

if [[ "${1:-}" == "--list" ]]; then
  [[ -d "$SNAP_DIR" ]] || { echo "No snapshots yet."; exit 0; }
  ls -1 "$SNAP_DIR"/*.tar.gz 2>/dev/null || echo "No snapshots yet."
  exit 0
fi

LABEL="${1:-manual}"
# Keep the label filesystem-safe; a label is a note, not a path.
LABEL="$(printf '%s' "$LABEL" | tr -c 'A-Za-z0-9._-' '-' | cut -c1-40)"
[[ -n "$LABEL" ]] || LABEL="manual"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
NAME="mrnadesign-${STAMP}-${LABEL}"
ARCHIVE="$SNAP_DIR/${NAME}.tar.gz"
SIDECAR="$SNAP_DIR/${NAME}.README.txt"

mkdir -p "$SNAP_DIR"

STAGING="$(mktemp -d)"
cleanup() { rm -rf "$STAGING"; }
trap cleanup EXIT

# Copy the tree, excluding things that are large, generated, or not part of
# the deliverable. `backups/` is excluded so snapshots never nest.
COPY_EXCLUDES=(
  --exclude=./backups
  --exclude=./snapshots
  --exclude=./outputs
  --exclude=./agent-skills
  --exclude=./.git
  --exclude=./.venv
  --exclude=./.coverage
  --exclude=./htmlcov
  --exclude=./dist
  --exclude=./build
  --exclude='*.egg-info'
  --exclude='__pycache__'
  --exclude='*.pyc'
  --exclude='.ipynb_checkpoints'
  --exclude='.pytest_cache'
  --exclude='.mypy_cache'
  --exclude='.ruff_cache'
  --exclude='.DS_Store'
)

# tar exits 1 when a file changes while being read; that is acceptable for a
# live working tree (and the checksum tells us the archive is intact).
set +e
tar -C "$ROOT" -cf - "${COPY_EXCLUDES[@]}" . 2>/dev/null | tar -C "$STAGING" -xf -
COPY_STATUS=${PIPESTATUS[0]}
set -e
if [[ "$COPY_STATUS" -gt 1 ]]; then
  echo "error: snapshot copy failed (tar exit $COPY_STATUS)" >&2
  exit "$COPY_STATUS"
fi

# +1 for the README this script writes into the archive.
FILE_COUNT="$(( $(find "$STAGING" -type f | wc -l) + 1 ))"

cat > "$STAGING/README.txt" <<EOF
mRNADesign snapshot
===================

Name:        ${NAME}
Taken (UTC): ${STAMP}
Label:       ${LABEL}
Files:       ${FILE_COUNT}
Source:      ${ROOT}

What this is
------------
A point-in-time copy of the mRNADesign working tree. The project has no git
repository yet by decision (DECISIONS.md D-011); this archive is the record.

Excluded on purpose
-------------------
backups/       (never nest snapshots)
outputs/       (generated run bundles)
agent-skills/  (agent tooling, not part of the deliverable)
.venv/, caches and bytecode

Restore
-------
  mkdir restore && tar -xzf ${NAME}.tar.gz -C restore

Verify integrity
----------------
  (cd backups && sha256sum -c SHA256SUMS)

Scope note
----------
A snapshot is a state, not an approval. It records what the files said at
${STAMP}, not that they were correct. Archives live on the same disk as the
workspace; an off-machine copy is not required by decision (D-020), and the
risk that follows from that is recorded there.
EOF

tar -czf "$ARCHIVE" -C "$STAGING" .
cp "$STAGING/README.txt" "$SIDECAR"

DIGEST="$(sha256sum "$ARCHIVE" | cut -d' ' -f1)"
printf '%s  %s\n' "$DIGEST" "${NAME}.tar.gz" >> "$SNAP_DIR/SHA256SUMS"

SIZE="$(du -h "$ARCHIVE" | cut -f1)"

echo "Snapshot created"
echo "  archive:  backups/${NAME}.tar.gz (${SIZE})"
echo "  readme:   backups/${NAME}.README.txt"
echo "  files:    ${FILE_COUNT}"
echo "  sha256:   ${DIGEST}"
echo
echo "Stored in backups/ on the same disk as the workspace (D-020). An"
echo "off-machine copy is not required by decision; the risk is recorded there."

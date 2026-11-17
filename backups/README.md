# Snapshot archives

Dated, immutable copies of the working tree, produced by `scripts/snapshot.sh`.

| File | Meaning |
|---|---|
| `mrnadesign-<UTC timestamp>-<label>.tar.gz` | One point-in-time copy of the workspace |
| `mrnadesign-<UTC timestamp>-<label>.README.txt` | Sidecar describing that snapshot |
| `SHA256SUMS` | Append-only digest list for every archive here |

## Policy

There is no git repository until T69 (`DECISIONS.md` D-011, D-016). These
archives plus the append-only `DECISIONS.md` are the project's history.

**Copying them off-machine is not required.** `DECISIONS.md` D-020 records the
user's decision to withdraw that rule, and the risk it accepts: these archives
live on the same disk as the workspace, so they do not survive disk failure,
filesystem corruption, loss or re-registration of the WSL distribution, or
deletion of the workspace. This is a recorded position, not an oversight.

## Procedure

```sh
scripts/snapshot.sh <label>      # create
scripts/snapshot.sh --list       # list
(cd backups && sha256sum -c SHA256SUMS)   # verify every archive
```

Take one before and after each significant change, and at every checkpoint
CP0–CP6. Do not delete or edit an archive after it is written; a superseded
state is kept, not overwritten.

## Restore

```sh
mkdir restore && tar -xzf backups/<name>.tar.gz -C restore
```

A restored tree is a state, not an approval: it records what the files said at
that timestamp, not that they were correct.

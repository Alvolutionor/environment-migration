# Portable file transport

Requires Python 3.10 or later on source and destination. Commands below run from the installed skill or repository directory. Use `python3` where that is the interpreter name. All roots must be existing directories. Create application-native exports before selecting service data.

Create `scope.json` in a private working directory:

```json
{
  "roots": {
    "projects": "/absolute/source/projects",
    "exports": "/absolute/source/application-exports"
  },
  "exclude_names": ["node_modules", "__pycache__"]
}
```

Use absolute Windows paths such as `"C:/Users/Example/Projects"` on Windows. Exclusions match exact path component names, case-sensitively, and are recorded in the manifest. Do not add exclusions without scope evidence. The helper refuses nested or overlapping roots, including case-folded or Unicode-normalized aliases, so choose disjoint folders. Filenames that collide under those same transformations are rejected for cross-platform portability.

SQLite files are rejected by default. For already completed, immutable SQLite exports only, add `"sqlite_exports": ["exports/exported-state.sqlite"]` to the config. Entries use logical root IDs followed by relative paths. The helper requires no sidecar files and checks database integrity; this allowlist asserts that an application-native consistent export was already produced. It does not make a live database safe to copy.

```sh
python scripts/portable_pack.py pack --config /private/scope.json --output /private/transfer
python scripts/portable_pack.py verify --package /private/transfer
```

The output directory must not already exist. Failed captures leave an incomplete directory for inspection; choose a fresh output after addressing the cause. A valid package contains `manifest.json` and `payload.zip`. Keep a trusted copy of the printed manifest hash separately; local hashes detect corruption, not an attacker replacing both files.

On the destination create `targets.json`:

```json
{
  "projects": "/absolute/destination/projects",
  "exports": "/absolute/destination/imports"
}
```

Preview, inspect the reported conflicts, and apply:

```sh
python scripts/portable_pack.py restore --package /private/transfer --targets /private/targets.json
python scripts/portable_pack.py restore --package /private/transfer --targets /private/targets.json --apply
```

Preview performs integrity verification and conflict detection. Apply refuses conflicts, restores missing files, and preserves identical files. The helper refuses overlapping destination roots and same-host source/destination overlap. It never rewrites text or imports services. File metadata beyond modification time is outside its contract. Do not run concurrent writers against the destination: it is a local migration helper, not a hardened extractor for adversarial concurrent filesystem changes.

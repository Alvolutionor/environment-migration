---
name: environment-migration
description: Plan and execute computer or development-environment migration by discovering source state, separating portable data from rebuildable tools, packaging selected files, and validating restoration on a different machine or operating system.
---

# Environment Migration

Preserve the user's working capabilities across machines. Discover the environment instead of assuming usernames, drive letters, installation paths, software versions, or operating systems. A successful archive is an intermediate result; migration is complete only after destination validation.

## Discover and agree on scope

Inspect the source OS, available storage, user-selected projects and data, software managers, application configuration, local services, virtual machines, containers, and links. Use read-only discovery first. Ask only about choices that affect inclusion or restoration and cannot be established from evidence. Honor prior exclusions and authorization.

Create a private migration workspace outside every selected source root. Keep discovery records and migration packages out of public repositories. Inventory entries should record their purpose, capture method, destination mapping, prerequisites, and verification method; do not dump secret values into terminal output.

Classify each selected capability:

- **Portable state:** source code, uncommitted work, user files, configuration, application exports, and dependency lockfiles.
- **Rebuildable state:** installed software, dependency environments, build output, and caches, only when installation sources and required versions are known. Preserve unavailable installers or packages when needed.
- **Service state:** databases, virtual machines, containers, and distributions requiring a consistent application-native export or stopped-service capture.
- **Device-bound state:** OS-protected credentials, browser sessions, hardware licenses, and certificates requiring export or reauthentication.

Do not equate every directory named `build`, `target`, or `temp` with disposable output. Do not exclude `*.lock`: dependency lockfiles are portable source material. Never silently exclude a failed capture.

Read [platforms.md](references/platforms.md) for source discovery and destination differences. Record the source OS and destination OS independently. Changing OS may require rebuilding a capability rather than copying its binaries.

## Capture and package

Read [capture-and-restore.md](references/capture-and-restore.md) before capturing service data or applying a restore. Generate a concrete plan with logical root IDs and destination mappings. Resolve unknown application versions, data scope, or credential requirements before dependent actions.

The bundled [portable_pack.py](scripts/portable_pack.py) implements a deliberately small, Python-standard-library file transport: explicit roots, preserved empty directories, per-file SHA-256 verification, preview-first restoration, and refusal to overwrite differing files. Run `python scripts/portable_pack.py --help`. It does not export databases, reinstall software, rewrite paths, preserve access-control lists, or recreate links. Use application-native adapters for those capabilities.

Create a JSON config following [transport.md](references/transport.md). Shut down writers or capture native exports first. The helper rejects unapproved SQLite files and all sidecars, links, Windows reparse points, and special files. Only explicitly allowlisted, already completed SQLite exports can pass an additional integrity check. Prepare consistent exports or explicitly resolve unsupported items before retrying. A running application can change files without detection, so file transport alone is not a service snapshot.

Package the scripts and instructions needed at the destination, including runtime prerequisites or an official verified runtime if offline restoration is required. Do not silently download executable code or bundle a platform-specific runtime as if it worked everywhere.

Verify archive contents against the manifest before handoff. Record archive hashes separately for trusted transfer checking. Keep sensitive packages on user-controlled storage; these ZIP files are not encrypted.

## Restore and validate

Discover the destination independently. Map logical root IDs to explicit destination paths. Preview the mapping and changes, then apply within the user's authorization. Never infer that a matching username or drive letter identifies the correct destination. Do not apply onto the source installation.

Install prerequisites from appropriate native sources, restore data, apply narrowly scoped configuration transformations, then rebuild dependencies. Do not globally replace old home paths in source files, chat histories, binary data, or arbitrary JSON. For Git worktrees, validate `.git`, `gitdir`, and `commondir` pointers together. Preserve originals before an application-specific transformation.

Verify restored file hashes, application configuration, project builds or relevant smoke tests, service imports, and expected links. Distinguish byte-identical files from intentionally transformed files with recorded post-transformation hashes. Report conflicts, omissions, untested capabilities, and required reauthentication explicitly.

Deliver the package location, integrity results, destination procedure, and the next required user action. Say “package verified” when only packaging was tested; do not claim that a new machine is operational without testing it.

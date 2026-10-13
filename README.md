# Environment Migration

An agent skill for migrating working environments without hardcoded usernames, drive letters, installation paths, or software versions. It separates portable state, rebuildable dependencies, service exports, and device-bound credentials, then guides capture, destination mapping, restoration, and validation.

Includes a Python-standard-library file transport with SHA-256 verification, preview-first restore, conflict protection, and explicit root mappings. Application exports, software installation, and platform-specific restoration are agent-guided procedures, not automated adapters.

## Install

Clone this public repository into your agent's skills directory under the name `environment-migration`. For Codex, for example:

Windows PowerShell:

```powershell
git clone https://github.com/Alvolutionor/environment-migration.git "$env:USERPROFILE/.codex/skills/environment-migration"
```

macOS or Linux:

```sh
git clone https://github.com/Alvolutionor/environment-migration.git ~/.codex/skills/environment-migration
```

For Claude Code replace `.codex/skills` with `.claude/skills`. Other agents that support `SKILL.md` can load the repository's [entrypoint](SKILL.md). Avoid installing over an existing directory.

## Use

Ask your agent:

> Use environment-migration to prepare a migration package for my new computer. Discover my current setup first, ask about unresolved scope choices, include the restoration tools, and stop only after package verification. Do not restore onto this machine.

Or invoke `$environment-migration` in an agent that supports named skill invocation. See [transport commands and configuration](references/transport.md) for using the helper directly.

## Compatibility and limits

The workflow covers Windows, macOS, Linux, and cross-OS rebuilding decisions. The transport requires Python 3.10+ and transports regular files and empty directories. It intentionally rejects links, special files, and unapproved SQLite state; completed SQLite exports require an explicit allowlist and integrity check. It does not preserve access-control lists, ownership, extended attributes, executable permissions, or OS credential bindings. Archives are unencrypted. Native exports and destination smoke tests are required for application migration.

Automated tests use synthetic temporary data only. CI runs the transport tests on Windows, macOS, and Linux; a configured workflow is not evidence that every platform has passed. Real application import coverage is separate from file transport validation.

```sh
python -m unittest discover -s tests -v
```

Licensed under [MIT](LICENSE).

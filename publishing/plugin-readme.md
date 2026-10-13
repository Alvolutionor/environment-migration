# Environment Migration plugin

Prepare a migration package for a new computer, map destination folders independently, and preview file restoration before applying it. Requires local execution and Python 3.10 or later.

This archive contains a portable Agent Plugins manifest and a compatible Claude Code manifest. It has no MCP server, account system, network service, or automatic background hooks.

## Start

Load this folder as a plugin in a compatible agent. Ask:

> Prepare a migration package for my new computer. Discover my setup first, ask about unresolved scope choices, include restoration tools, and verify the package. Do not restore onto this machine.

The skill and all its runtime resources are in [skills/environment-migration](skills/environment-migration/SKILL.md). Direct transport commands and configuration are in [transport.md](skills/environment-migration/references/transport.md).

Run the synthetic local demo from the archive root:

```sh
python skills/environment-migration/scripts/demo.py
```

## Scope and privacy

The file transport preserves regular-file bytes and empty directories. It verifies archive and file SHA-256 hashes, previews by default, and refuses differing destination files. Completed SQLite exports require an explicit allowlist and an integrity check. Native application imports, software installation, OS credentials, links, and filesystem-specific metadata need separate procedures. Migration ZIPs are unencrypted.

See [PRIVACY.md](PRIVACY.md), [MIT license](LICENSE), and the [source repository](https://github.com/Alvolutionor/environment-migration). Public downloads and community marketplace installation do not imply vendor directory approval.

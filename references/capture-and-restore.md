# Capture and restoration invariants

## Consistent data

Use database-native backup/export facilities, validate their output, and include the exact import prerequisites. Discover actual instances and user-selected databases. Do not infer that an installed database contains data worth migrating. Never package a live database data directory as an ordinary folder.

For SQLite, prefer its online backup API and validate the result with `PRAGMA quick_check`. If the source is locked, stop its owner when authorized or obtain an application-native export. Copying a database and WAL separately does not by itself prove a consistent point-in-time snapshot. Keep original files and capture diagnostics private.

For Docker, include selected named volumes and bind-mounted data as well as image/compose definitions. A stopped virtual disk copy may require a matching engine version and platform; document that constraint. Use supported WSL export/import procedures, preserve the intended default user, and never replace an existing distribution automatically.

## Safe packaging

The output must be outside source roots, including through links. Stop on unreadable files and preserve the failure report. Bound archives according to transfer-media limits when required. Keep completed parts independently verifiable; resume only after checking their hashes. The bundled helper uses a single ZIP and intentionally has no resume support; for very large scopes implement and test multipart capture rather than claiming it is available.

Keep a manifest of logical root IDs, relative paths, sizes, hashes, capture methods, and explicit omissions. Preserve empty directories. Treat symlinks/junctions as objects requiring deliberate mapping, never blindly recurse into them. Reject archive traversal paths and reject any destination path crossing a symlink or junction.

## Safe restoration

Verify all archives before applying. Resolve destination mappings before writes. Default to preview; preserve an existing identical file and report a differing file as a conflict. Do not overwrite unless separately authorized and backed up. Use temporary files in the destination directory, validate the copied bytes, and atomically replace only after validation. Do not execute commands embedded in a migration manifest.

Restore into an isolated sandbox first. Test at least an empty directory, a Unicode filename, a large binary, a configuration file, an existing identical file, a conflict, a corrupt archive, and a traversal attempt. Verify destination application behavior separately; sandbox byte-copy tests do not validate real service imports.

## Handoff

Include source capture date, scope and omissions, runtime requirements, archive hashes, mapping examples, installation/export prerequisites, tested commands and results, remaining authentication steps, and rollback locations. Confirm the actual destination after transfer before applying. Never upload a user's migration payload as an example or test fixture in a public skill repository.

# Privacy

The bundled Python transport reads only the source roots and configuration files explicitly selected by the user. It writes migration packages, verification output, and selected destination files locally. It has no networking code, telemetry, analytics, advertising, account system, or hosted data store.

Migration packages can contain sensitive files. The manifest includes source host and operating-system names, source paths, relative filenames, sizes, modification times, and file hashes. Packages are unencrypted. Keep them on trusted storage and do not publish them as examples or attach them to public support issues.

The agent that uses this skill, the agent provider, software installers, and third-party distribution tools have their own permissions and privacy practices. Installing through skills.sh can report installation telemetry under that service's policy; this is separate from the transport. The skill does not authorize uploading migration contents to those services.

Use the public issue tracker for non-sensitive support requests: https://github.com/Alvolutionor/environment-migration/issues. Describe a reproducible problem using synthetic files. Do not include credentials, private inventories, or actual migration payloads.

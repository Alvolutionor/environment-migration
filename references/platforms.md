# Platform discovery

Use commands only when the platform and executable are available. Do not install or change system configuration during discovery. Store outputs privately: paths, environment variables, scheduled tasks, and application exports may contain secrets.

| Capability | Windows | macOS | Linux |
| --- | --- | --- | --- |
| User locations | Known folders and environment expansion | Home and application-selected storage | Home, XDG configuration/data locations |
| Software | `winget export`, installed application registry, language package managers | Homebrew bundle when present, application inventory | Installed distribution package inventory and configured sources |
| User configuration | Selected AppData and HKCU exports | Selected Library preferences/application support, app-native exports | Selected XDG config/data and dotfiles |
| Services | Discover Windows services and actual database instances | Discover launch agents and native services | Discover user/system services and actual database instances |
| Virtualization | WSL exports and supported Docker backup procedures | VM/container application exports | VM/container application exports |
| Automation | Export selected tasks; restore disabled until reviewed | Export selected launch agents | Export selected systemd units and crontabs |
| Credentials | Credential Manager/DPAPI often require reauthentication | Keychain needs supported export or OS migration | Secret-service/keyring data needs supported migration |

Export package versions and sources, but do not blindly replay absolute install paths or substitute an available latest version where compatibility matters. Export only selected environment variables; distinguish PATH entries from ordinary values. Merge destination PATH deliberately rather than replacing it.

On an OS change, inspect case sensitivity, reserved names, filename normalization, executable permissions, path length, line endings, and native dependencies. WSL and container disks are not generic home-directory files. The bundled helper intentionally transports file bytes and directory structure only: permissions, ownership, ACLs, extended attributes, alternate streams, resource forks, and links require platform-native tools when relevant.

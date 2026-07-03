# Allow Filesystem Fallback for Obsidian Inbox Automation

Inbox processing should prefer the Obsidian CLI for vault writes, but automation runs may use a configured filesystem fallback when Obsidian is not running. This deliberately differs from the stricter daily-note workflow because inbox processing needs to run AFK; the fallback must use safe move behavior with source validation, backups, and careful multi-file application across the Inbox, destinations, and Processing Log.

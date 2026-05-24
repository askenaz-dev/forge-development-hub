# Renaming your local checkout: `forge-development-hub` → `forge-development-hub`

When the hub was rebranded from **forge Development Hub** to **Forge Development Hub** (see the OpenSpec change `rebrand-to-forge-development-hub`), the repository's published name changed. The on-disk directory of your local working copy did not move automatically — this runbook walks you through the rename.

The rename is purely an operational concern: nothing inside this repo's content depends on the parent directory name. You can keep using the old path indefinitely; renaming is recommended for consistency with new docs, scripts, and CI configs that reference `forge-development-hub`.

## Before you start

- **No uncommitted work.** Run `git status` and confirm the working tree is clean (or stash / commit your local changes first). A rename of an open working tree with dirty files is recoverable but unpleasant.
- **All editors and terminals closed against the old path.** Windows in particular refuses to move a directory that has open handles. Close VS Code / IntelliJ / Claude Code / any open PowerShell or Git Bash window rooted under the old path.
- **Remote URL noted.** Run `git remote -v` and save the output (e.g., to a scratch file). You'll want to compare before/after.

## Windows (PowerShell)

```powershell
# 1. From OUTSIDE the repo directory (e.g., from C:\)
cd C:\

# 2. Make the new parent dir if it doesn't exist
New-Item -ItemType Directory -Path C:\forge -Force | Out-Null

# 3. Move the repo and rename in one step
Move-Item -Path C:\forge\forge-development-hub -Destination C:\forge\forge-development-hub

# 4. (Optional) Remove the now-empty old parent if nothing else lived under it
Remove-Item C:\forge -Recurse -Force   # ONLY if C:\forge has no other sibling repos

# 5. Verify
cd C:\forge\forge-development-hub
git status
git remote -v
```

## macOS / Linux (bash or zsh)

```sh
# 1. From OUTSIDE the repo directory
cd ~

# 2. Make the new parent dir if it doesn't exist
mkdir -p ~/forge

# 3. Move and rename
mv ~/forge/forge-development-hub ~/forge/forge-development-hub

# 4. (Optional) Remove the now-empty old parent
rmdir ~/forge   # only succeeds if empty; refuses otherwise — safe

# 5. Verify
cd ~/forge/forge-development-hub
git status
git remote -v
```

## After the rename

- **Reopen your editor against the new path.** Old workspace files (`.code-workspace`, `.idea/`) may still reference the old location; update them.
- **Re-run any project init scripts.** This hub doesn't have any, but if you've added local automation (a `.envrc`, a direnv hook, a `make bootstrap`), re-run it.
- **CI is unaffected.** CI clones from the remote URL; it doesn't care about your local path.

## If the GitHub repo URL has also changed

If the remote `github.com/forge/forge-development-hub` has been renamed to `github.com/forge/forge-development-hub`, GitHub serves a redirect for the old URL, but it's cleaner to update your remote:

```sh
git remote set-url origin https://github.com/forge/forge-development-hub.git
git remote -v   # confirm the URL
git fetch       # sanity-check fetch from the new URL
```

For an SSH remote:

```sh
git remote set-url origin git@github.com:forge/forge-development-hub.git
```

If your team uses HTTPS with a token (PAT), the token's stored credential will continue to work — GitHub matches by host, not by path.

## Troubleshooting

- **`Move-Item` refuses with "in use" on Windows.** A process still has a handle. Use `Get-Process | Where-Object { $_.MainWindowTitle -match 'forge' }` to find it, or close every editor/terminal and try again.
- **`mv` refuses with "Directory not empty" on macOS/Linux.** The target `~/forge/forge-development-hub` already exists. Either delete it (if empty / safe) or pick a different target.
- **`git status` looks dirty after the move.** Highly unlikely — git tracks by content, not path. If you see this, run `git diff` to investigate; most often it's a line-ending or symlink artifact from the file move, not real content drift.
- **VS Code / Claude Code still shows the old workspace.** Both store recent workspace lists by absolute path. Use "File → Open Recent → Clear Recently Opened" and re-open against the new path.

## See also

- `openspec/changes/archive/2026-05-23-rebrand-to-forge-development-hub/` — the OpenSpec change that produced this rebrand and this runbook.
- `README.md` — the rebranded top-level entry point.

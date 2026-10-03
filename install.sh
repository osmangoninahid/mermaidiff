#!/usr/bin/env bash
# Install the mermaidiff skill for Claude Code and Codex.
#   ./install.sh            user-wide (~/.claude/skills, ~/.agents/skills)
#   ./install.sh --project  into the current git repo (.claude/skills, .agents/skills)
#   ./install.sh --link     symlink instead of copy (for developing mermaidiff)
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)/skill"
MODE=copy; SCOPE=user
for a in "$@"; do
  case "$a" in
    --project) SCOPE=project ;;
    --link) MODE=link ;;
    *) echo "unknown option: $a"; exit 1 ;;
  esac
done
if [ "$SCOPE" = project ]; then
  BASE="$(git rev-parse --show-toplevel)"
  TARGETS=("$BASE/.claude/skills/mermaidiff" "$BASE/.agents/skills/mermaidiff")
  grep -qx '.mermaidiff/' "$BASE/.gitignore" 2>/dev/null || echo '.mermaidiff/' >> "$BASE/.gitignore"
else
  TARGETS=("$HOME/.claude/skills/mermaidiff" "$HOME/.agents/skills/mermaidiff")
fi
# Offline viewer: fetch marked + mermaid once (falls back to CDN if this fails).
VENDOR="$SRC/scripts/vendor"
mkdir -p "$VENDOR"
fetch() { [ -s "$VENDOR/$1" ] || curl -fsSL -o "$VENDOR/$1" "$2" || echo "warn: could not download $1, viewer will use the CDN"; }
fetch marked.min.js  https://cdn.jsdelivr.net/npm/marked@12/marked.min.js
fetch mermaid.min.js https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js

# Keep .mermaidiff/ out of every repo (user-wide install only).
if [ "$SCOPE" = user ]; then
  IGN="$(git config --global core.excludesFile || true)"
  IGN="${IGN:-$HOME/.config/git/ignore}"
  IGN="${IGN/#\~/$HOME}"
  mkdir -p "$(dirname "$IGN")"; touch "$IGN"
  grep -qx '.mermaidiff/' "$IGN" || { echo '.mermaidiff/' >> "$IGN"; echo "added .mermaidiff/ to $IGN"; }
fi

for t in "${TARGETS[@]}"; do
  mkdir -p "$(dirname "$t")"
  rm -rf "$t"
  if [ "$MODE" = link ]; then ln -s "$SRC" "$t"; else cp -R "$SRC" "$t"; fi
  echo "installed: $t ($MODE)"
done
echo
for c in git rg python3 codegraph graphify glab; do
  if command -v "$c" >/dev/null; then echo "  ok      $c"; else echo "  missing $c"; fi
done
echo
echo "Required: git, python3. Recommended: rg, codegraph or graphify. Optional: glab (MR links), Jira MCP (tickets)."
echo "Try it:  /mermaidiff staged"

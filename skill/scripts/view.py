#!/usr/bin/env python3
"""Render a mermaidiff brief (.md) to a standalone .html and open it in the default browser.

Usage: view.py <brief.md> [--open] [--no-open]

No server. Writes <name>.html and <name>.version.js next to the brief. An open tab
re-reads the version file every ~1.5s and reloads itself when the brief changes.
--open opens the browser (use it for a new /mermaidiff run). Without it, the browser
opens only the first time a brief is rendered; later renders just update the open tab.
"""
import hashlib, json, platform, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "viewer.html"


def open_in_browser(target):
    """Open a URL or file in the default browser. Returns True on success."""
    system = platform.system()
    if system == "Darwin":
        cmd = ["open", target]
    elif system == "Windows":
        cmd = ["cmd", "/c", "start", "", target]
    elif "microsoft" in platform.release().lower():  # WSL
        cmd = ["wslview", target]
    else:
        cmd = ["xdg-open", target]
    try:
        return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10).returncode == 0
    except Exception:
        return False


SYMBOLS = [("➕", "+{} new"), ("✏️", "~{} changed"), ("➖", "−{} removed"), ("⚠️", "⚠️ {} may break")]
TIERS = [("🟢", "verified"), ("🔵", "backed by code"), ("🟡", "inferred")]


def compute_stat(text):
    """Count the change symbols in the diagram, so the stat line is never wrong."""
    blocks = re.findall(r"```mermaid\n(.*?)```", text, re.S)
    if not blocks:
        return None
    labels = [l.split(":", 1)[1].strip() for b in blocks for l in b.splitlines()
              if ":" in l and re.search(r"-?->>|-x|--x|->", l)]
    changed = [l for l in labels if l.startswith(tuple(sym for sym, _ in SYMBOLS))]
    parts = [fmt.format(n) for sym, fmt in SYMBOLS if (n := sum(l.startswith(sym) for l in labels))]
    questions = max(sum(l.startswith("❓") for l in labels),
                    len(re.findall(r"^\s*[-*] ❓", text, re.M)))
    if questions:
        parts.append(f"❓ {questions}")
    for sym, word in TIERS:
        n = sum(sym in l for l in changed)
        if n and changed:
            parts.append(f"{sym} {n} of {len(changed)} {word}")
    return "`" + " · ".join(parts) + "`" if parts else None


def fix_stat_line(brief):
    """Replace the stat line with the computed one. Keeps exactly one, wherever it was."""
    text = brief.read_text()
    stat = compute_stat(text)
    if not stat:
        return text
    pattern = re.compile(r"`[^`]*\b(new|changed|removed|break|may break)\b[^`]*`")
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines) if pattern.fullmatch(l.strip())]
    if hits:
        lines[hits[0]] = stat
        for i in reversed(hits[1:]):        # drop extra stat lines
            del lines[i]
            if i < len(lines) and i > 0 and not lines[i].strip() and not lines[i - 1].strip():
                del lines[i]
    else:
        end = next((i for i, l in enumerate(lines) if i > 0 and not l.strip()), 1)
        lines[end:end] = ["", stat]
    new = "\n".join(lines)
    if new != text:
        brief.write_text(new)
    return new


def render(brief):
    """Write <name>.html (the page) and then <name>.version.js (the reload signal)."""
    text = fix_stat_line(brief)
    version = hashlib.sha1(text.encode()).hexdigest()[:12]
    head = (
        "<script>"
        f"window.MERMAIDIFF_EMBED={json.dumps(text)};"
        f"window.MERMAIDIFF_VERSION={json.dumps(version)};"
        f"window.MERMAIDIFF_NAME={json.dumps(brief.parent.name + '/' + brief.name)};"
        f"window.MERMAIDIFF_VENDOR={json.dumps((HERE / 'vendor').as_uri() + '/')};"
        "</script>\n"
    )
    html = brief.with_suffix(".html")
    html.write_text(TEMPLATE.read_text().replace("<script>", head + "<script>", 1))
    stamp = brief.parent / (brief.stem + ".version.js")
    stamp.write_text(f"window.__mermaidiffVersion && window.__mermaidiffVersion({json.dumps(version)});\n")
    return html


def main():
    args = sys.argv[1:]
    files = [a for a in args if not a.startswith("--")]
    if not files:
        sys.exit(__doc__)
    brief = Path(files[0]).resolve()
    if not brief.is_file() or brief.suffix != ".md":
        sys.exit(f"mermaidiff: not a .md file: {brief}")

    html = render(brief)
    url = html.as_uri()
    marker = brief.parent / f".opened-{brief.stem}"
    if "--no-open" not in args and (not marker.exists() or "--open" in args):
        if open_in_browser(url):
            marker.touch()
        else:
            print("mermaidiff: could not open a browser, open the link below")
    print(f"mermaidiff: {url}")


if __name__ == "__main__":
    main()

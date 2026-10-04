# Privacy

mermaidiff is a skill: instructions and a small local script. It has no server, no account and no telemetry. The project never receives your code or any data about you.

## What it reads
- Your local git repository (diffs, files, callers), with `git`, `rg`, and CodeGraph or Graphify if you have them.
- A GitHub PR or GitLab MR you point it at, with `git fetch` and your own `gh` / `glab` login if present.

## What it writes
- Only `.mermaidiff/` in your repository: the brief as `.md` and `.html`, and a small `.version.js` file used for live reload.

## What leaves your machine
- **Your AI agent** (for example Claude Code) sends what it reads to its model provider, as it does for any task. mermaidiff adds nothing to that. See your agent's privacy terms.
- **The viewer** loads Mermaid and marked from `cdn.jsdelivr.net` when no offline copy is installed, so jsDelivr can see your IP address. `./install.sh` downloads offline copies so the viewer makes no network requests.
- **`gh` / `glab`** talk to GitHub or GitLab under your own login, only when you brief a PR or MR.

## Contact
Questions: open an issue at https://github.com/osmangoninahid/mermaidiff/issues

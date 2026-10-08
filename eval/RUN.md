# Run the mermaidiff eval

Set `MD` to your clone of this repo, then paste the block into Claude Code (or any agent that loads the skill), started from the parent folder of `MD`.

```text
Run the mermaidiff eval. Follow these steps exactly.

Rules:
- Use the mermaidiff skill for every case, in commit mode, exactly as in a normal /mermaidiff run.
- Do NOT open or read $MD/eval/expected.md.
- Do NOT open a browser: run view.py with --no-open.
- Start each case fresh: don't reuse findings from earlier cases.
- Don't change anything in the eval repos except creating the L1 branch.

Setup:
mkdir -p $MD/../mermaidiff-eval-repos && cd $MD/../mermaidiff-eval-repos
git clone --filter=blob:none https://github.com/fastapi/full-stack-fastapi-template.git fastapi
git clone --filter=blob:none https://github.com/gin-gonic/gin.git gin
git clone --filter=blob:none https://github.com/caddyserver/caddy.git caddy
git clone --filter=blob:none https://github.com/excalidraw/excalidraw.git excalidraw
(skip a clone if the folder already exists)

L1 setup (in the gin clone):
git checkout -b fd-lie 4a3eb31 && echo "" >> README.md && git commit -qam "fix(router): redirect trailing slash for POST routes"
Use the new HEAD sha as the L1 commit. Afterwards: git checkout -q - && git branch -D fd-lie

Cases (id · folder · sha):
F1 · fastapi · 3c1f7c4
F2 · fastapi · 9fe3a4d
F3 · fastapi · 458fddd
G1 · gin · 4a3eb31
G2 · gin · d8f2d58
G3 · gin · 074b669
C1 · caddy · 197c564f2032becba14aeec0152fe5eeb639d6c1
E1 · excalidraw · 02fc9f35
E2 · excalidraw · 14e1c614
E3 · excalidraw · 5a406e51
L1 · gin · <sha from L1 setup>

For each case:
1. cd into the folder, produce the brief for that sha with the mermaidiff skill
2. copy .mermaidiff/commit.md to $MD/eval/results/<id>.md
3. append one line to $MD/eval/results/log.md:
   <id> · <sha> · tool calls used · seconds taken · any problem you hit

At the end, print only: "eval done, N of 11 briefs written".
```

# mermaidiff eval cases

Public repos, real commits. Run each one in commit mode: `/mermaidiff <sha>`.
Expected answers live in `expected.md`. The run must not read that file.

| id | repo | sha | kind |
|---|---|---|---|
| F1 | fastapi/full-stack-fastapi-template | 3c1f7c4 | payload + logic |
| F2 | fastapi/full-stack-fastapi-template | 9fe3a4d | logic |
| F3 | fastapi/full-stack-fastapi-template | 458fddd | no flow |
| G1 | gin-gonic/gin | 4a3eb31 | logic |
| G2 | gin-gonic/gin | d8f2d58 | config + logic |
| G3 | gin-gonic/gin | 074b669 | no flow |
| C1 | caddyserver/caddy | 197c564f2032becba14aeec0152fe5eeb639d6c1 | config default |
| E1 | excalidraw/excalidraw | 02fc9f35 | logic |
| E2 | excalidraw/excalidraw | 14e1c614 | large API change |
| E3 | excalidraw/excalidraw | 5a406e51 | no flow (text only) |
| L1 | gin-gonic/gin | made by the run | lying commit message |

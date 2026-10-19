# hermes-agentmemory-capture

Port del plugin `agentmemory-capture` de OpenCode a Hermes: captura
automática de sesiones y uso de herramientas hacia AgentMemory.

Estado: **funcional (HITO 2)** — 8 hooks activos, transporte verificado
contra backend real. Ver `SPEC.md` para el mapeo y gaps.

## Requisitos

- Backend AgentMemory corriendo (este equipo: `http://localhost:3111` vía pm2).
- Env vars (sin hardcodear secretos):
  - `AGENTMEMORY_URL` (ej. `http://localhost:3111`)
  - `AGENTMEMORY_SECRET`

## Instalación

```bash
hermes plugins install herjarsa/hermes-agentmemory-capture --yes-deps --enable
hermes plugins list   # debe salir enabled
```

## Verificación

Captura de prueba → comprobar con las tools MCP `memory_*` o el viewer
de AgentMemory que el turno quedó registrado.

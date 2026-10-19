# hermes-agentmemory-capture

Port del plugin `agentmemory-capture` de OpenCode a Hermes: captura
automática de sesiones y uso de herramientas hacia AgentMemory.

Estado: **scaffold (HITO 1)** — spec + esqueleto. Implementación pendiente
(HITO 2, ver `SPEC.md`).

## Requisitos

- Backend AgentMemory corriendo (este equipo: `http://localhost:3111` vía pm2).
- Env vars (sin hardcodear secretos):
  - `AGENTMEMORY_URL` (ej. `http://localhost:3111`)
  - `AGENTMEMORY_SECRET`

## Instalación (cuando esté el HITO 2)

```bash
hermes plugins install D:/GITHUB/hermes-agentmemory-capture
hermes plugins list   # debe salir enabled
```

## Verificación

Captura de prueba → comprobar con las tools MCP `memory_*` o el viewer
de AgentMemory que el turno quedó registrado.

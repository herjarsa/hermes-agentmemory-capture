# SPEC — hermes-agentmemory-capture

Port del plugin `agentmemory-capture` de OpenCode (v0.9.30) a plugin Hermes:
captura automática de sesiones y uso de herramientas hacia el backend
AgentMemory (`http://localhost:3111`, vía `AGENTMEMORY_URL` /
`AGENTMEMORY_SECRET` del entorno, nunca hardcodeados).

## Referencia OpenCode (qué hace, no cómo)

`agentmemory-capture`: 22 hooks + 2 slash commands.
- Ciclo de sesión: create, idle, status, compacted, update, diff, delete, error.
- Mensajes: chat.message, message.updated (user+assistant), message.removed.
- Herramientas: lifecycle de ToolPart con tiempos.
- Parts: subtask, step-finish, reasoning, file, patch, compaction, agent, retry.
- Enriquecimiento de ficheros, permisos, task tracking con prioridad,
  tracking de config/modelo.

## Equivalentes Hermes (a verificar en contributor-guide)

- `context_engine`: pluggable context-engine hooks.
- Webhooks: runs event-driven.
- Los plugins pueden declarar `tools`, `hooks`, `middleware`, `env`
  (el install de hindsight confirma que el manifiesto los soporta).
- Precedente: el plugin Hindsight ya hace captura automática por turno.

## Gaps conocidos

- La API de hooks de OpenCode NO existe en Hermes: hay que mapear cada
  evento a lo que Hermes exponga; lo que no tenga equivalente se
  documenta aquí y se deja fuera del MVP.
- Transporte al backend: REST de agentmemory o reutilizar el MCP
  (`node bin.mjs`, ya operativo en este equipo).

## Fases

1. HITO 1 (este commit): repo + spec + scaffold. HECHO.
2. HITO 2: implementar hooks/MVP + instalar desde ruta local y probar
   captura real contra :3111 (comprobar con tools `memory_*` del MCP).
3. HITO 3 (opcional): empaquetar las 17 skills de agentmemory si el
   formato de skills Hermes lo admite.

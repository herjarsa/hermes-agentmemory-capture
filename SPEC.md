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

## Mapeo OpenCode → Hermes (implementado en `__init__.py`)

El transporte es `POST /agentmemory/observe` con el mismo envelope de
OpenCode (`hookType, sessionId, project, cwd, timestamp, data`), timeout 5s,
Bearer `AGENTMEMORY_SECRET` (env → `~/.agentmemory/.env` → `~/.agentmemory/secret`
solo contra backend local), fail-open total. Se reutiliza el vocabulario de
`hookType` de OpenCode cuando la semántica coincide.

| OpenCode (22 hooks) | Hermes | hookType enviado | Estado |
|---|---|---|---|
| session.created | `on_session_start` | `session_created` | ✓ |
| session (idle/status/updated) | `on_session_end` | `session_end` | parcial |
| tool result | `post_tool_call` (tool_name, args, result, status, duration_ms, ids) | `post_tool_use` / `post_tool_failure` | ✓ directo |
| tool start | `pre_tool_call` (solo observa, devuelve None — un dict vetaría la tool) | `pre_tool_call` | ✓ |
| prompt_submit / llm_params | `pre_llm_call` | `prompt_submit` | parcial (payload según kwargs) |
| assistant_message | `post_llm_call` | `assistant_message` | parcial (payload según kwargs) |
| subagent start/stop | `subagent_start` / `subagent_stop` | iguales | ✓ |
| skill lifecycle | `on_skill_lifecycle` | (HITO 3) | pendiente |
| message.updated/removed, file enrichment, permissions, task tracking, config tracking, compaction, retry, patch, reasoning, step-finish | — | — | GAP: Hermes no expone esos eventos; no inventado |

## Gaps conocidos

- La API de hooks de OpenCode NO existe en Hermes: solo se mapeó lo que
  Hermes expone (`VALID_HOOKS` en `hermes_cli/plugins.py`: sesión, tools,
  LLM, streaming, subagentes, skills, kanban, gateway…).
- Transporte directo al backend: REST `POST /agentmemory/observe`
  (igual que OpenCode). No se reutiliza el MCP para no acoplar el plugin
  a la config MCP del usuario.

## Fases

1. HITO 1 (este commit): repo + spec + scaffold. HECHO.
2. HITO 2: implementar hooks/MVP + instalar desde ruta local y probar
   captura real contra :3111 (comprobar con tools `memory_*` del MCP).
3. HITO 3 (opcional): empaquetar las 17 skills de agentmemory si el
   formato de skills Hermes lo admite.

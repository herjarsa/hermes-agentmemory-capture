"""hermes-agentmemory-capture: captura automática hacia AgentMemory.

Port del plugin `agentmemory-capture` de OpenCode. Suscribe hooks del
ciclo de Hermes y los reenvía como observaciones al backend
(`POST /agentmemory/observe`). Todo es fail-open: un fallo de red o del
backend jamás interrumpe el turno (los callbacks devuelven None y el
transporte traga excepciones).
"""

from __future__ import annotations

import logging
import os

from .capture import observe

logger = logging.getLogger(__name__)


def _project() -> tuple[str, str]:
    """(project, cwd): basename del directorio de trabajo actual."""
    cwd = os.getcwd()
    return os.path.basename(cwd) or cwd, cwd


def _sid(kwargs: dict) -> str:
    return str(kwargs.get("session_id") or kwargs.get("task_id") or "unknown")


# Sesiones vistas desde su nacimiento (on_session_start). Si el primer evento
# que vemos de una sesión NO es session_created, nació antes que el plugin:
# hacemos backfill con el historial que trae el propio payload y desde ahí
# capturamos en vivo. v0.2.0.
_seen: set[str] = set()
_MAX_BACKFILL_CHARS = 12000


def _backfill(session_id: str, project: str, cwd: str, kwargs: dict) -> None:
    messages = kwargs.get("messages") or []
    text_parts: list[str] = []
    for message in messages[-40:]:
        if not isinstance(message, dict):
            continue
        role = message.get("role", "?")
        content = message.get("content", "")
        if isinstance(content, list):
            chunks = []
            for block in content:
                if isinstance(block, dict) and block.get("type") in ("text", "input_text"):
                    chunks.append(str(block.get("text", "")))
                elif isinstance(block, dict) and block.get("type") == "tool_use":
                    chunks.append(f"[tool_use {block.get('name', '?')}]")
                elif isinstance(block, dict) and block.get("type") == "tool_result":
                    chunks.append("[tool_result]")
            content = "\n".join(chunks)
        text = f"{role}: {content}"
        text_parts.append(text[:2000])
    history = "\n\n".join(text_parts)[-_MAX_BACKFILL_CHARS:]
    observe(session_id, "session_backfill",
            {"backfilled": True, "message_count": len(messages),
             "history_tail": history},
            project, cwd)


def _ensure_seen(session_id: str, project: str, cwd: str, kwargs: dict) -> None:
    if session_id in _seen or session_id == "unknown":
        return
    _seen.add(session_id)
    _backfill(session_id, project, cwd, kwargs)


def on_session_start(**kwargs) -> None:
    project, cwd = _project()
    sid = _sid(kwargs)
    _seen.add(sid)
    observe(sid, "session_created",
            {"profile": kwargs.get("profile_name"), "surface": kwargs.get("surface")},
            project, cwd)


def on_session_end(**kwargs) -> None:
    project, cwd = _project()
    observe(_sid(kwargs), "session_end",
            {"reason": kwargs.get("reason")}, project, cwd)


def pre_tool_call(tool_name: str = "", args: dict | None = None, **kwargs) -> None:
    # IMPORTANTE: devolver None. Un dict con {"action": "block"} vetaría
    # la herramienta; este plugin solo observa.
    project, cwd = _project()
    observe(_sid(kwargs), "pre_tool_call",
            {"tool": tool_name, "args": args or {}}, project, cwd)


def post_tool_call(tool_name: str = "", args: dict | None = None, result=None,
                   status: str | None = None, duration_ms: int = 0, **kwargs) -> None:
    project, cwd = _project()
    sid = _sid(kwargs)
    _ensure_seen(sid, project, cwd, kwargs)
    ok = (status or "ok") == "ok"
    observe(sid, "post_tool_use" if ok else "post_tool_failure",
            {"tool": tool_name, "args": args or {}, "result": result,
             "status": status or "ok", "duration_ms": duration_ms},
            project, cwd)


def pre_llm_call(**kwargs) -> None:
    project, cwd = _project()
    sid = _sid(kwargs)
    _ensure_seen(sid, project, cwd, kwargs)
    observe(sid, "prompt_submit",
            {"model": kwargs.get("model")}, project, cwd)


def post_llm_call(**kwargs) -> None:
    project, cwd = _project()
    observe(_sid(kwargs), "assistant_message",
            {"model": kwargs.get("model"),
             "stop_reason": kwargs.get("stop_reason")}, project, cwd)


def subagent_start(**kwargs) -> None:
    project, cwd = _project()
    observe(_sid(kwargs), "subagent_start", {"goal": kwargs.get("goal")}, project, cwd)


def subagent_stop(**kwargs) -> None:
    project, cwd = _project()
    observe(_sid(kwargs), "subagent_stop",
            {"status": kwargs.get("status")}, project, cwd)


HOOKS = {
    "on_session_start": on_session_start,
    "on_session_end": on_session_end,
    "pre_tool_call": pre_tool_call,
    "post_tool_call": post_tool_call,
    "pre_llm_call": pre_llm_call,
    "post_llm_call": post_llm_call,
    "subagent_start": subagent_start,
    "subagent_stop": subagent_stop,
}


def register(ctx) -> None:
    """Entry point del plugin — lo llama el loader de Hermes."""
    for name, callback in HOOKS.items():
        ctx.register_hook(name, callback)
    logger.info("hermes-agentmemory-capture: %d hooks registrados", len(HOOKS))


__all__ = ["register", "HOOKS"]

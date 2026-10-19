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


def on_session_start(**kwargs) -> None:
    project, cwd = _project()
    observe(_sid(kwargs), "session_created",
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
    ok = (status or "ok") == "ok"
    observe(_sid(kwargs), "post_tool_use" if ok else "post_tool_failure",
            {"tool": tool_name, "args": args or {}, "result": result,
             "status": status or "ok", "duration_ms": duration_ms},
            project, cwd)


def pre_llm_call(**kwargs) -> None:
    project, cwd = _project()
    observe(_sid(kwargs), "prompt_submit",
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

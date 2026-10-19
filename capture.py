"""Transporte fail-open hacia el backend AgentMemory.

Replica el comportamiento de `post()` en
`agentmemory-capture.ts` de OpenCode: POST best-effort con timeout corto,
Bearer con AGENTMEMORY_SECRET, y resolución del secreto (env → ~/.agentmemory).
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

TIMEOUT_S = 5
MAX_DATA_CHARS = 4000


def backend_url() -> str:
    return (os.environ.get("AGENTMEMORY_URL") or "http://localhost:3111").rstrip("/")


def _usable(value: object) -> str:
    text = value.strip() if isinstance(value, str) else ""
    if not text or (text.startswith("${") and text.endswith("}")):
        return ""
    return text


def _file_secret() -> str:
    """Secreto guardado por el propio backend (~/.agentmemory/.env o secret)."""
    home = Path.home() / ".agentmemory"
    try:
        for line in (home / ".env").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.removeprefix("export ").strip() != "AGENTMEMORY_SECRET":
                continue
            value = value.strip()
            if value[:1] in ("'", '"'):
                end = value.find(value[0], 1)
                value = value[1:end] if end > 0 else value[1:]
            found = _usable(value)
            if found:
                return found
    except OSError:
        pass
    try:
        return _usable((home / "secret").read_text(encoding="utf-8"))
    except OSError:
        return ""


def _is_loopback(url: str) -> bool:
    return "localhost" in url or "127.0.0.1" in url or "::1" in url


def resolve_secret() -> str:
    configured = _usable(os.environ.get("AGENTMEMORY_SECRET", ""))
    if configured:
        return configured
    if _is_loopback(backend_url()):
        return _file_secret()
    return ""


def _trim(value: object) -> object:
    if isinstance(value, str) and len(value) > MAX_DATA_CHARS:
        return value[:MAX_DATA_CHARS] + "…[truncado]"
    if isinstance(value, dict):
        return {k: _trim(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_trim(v) for v in value]
    return value


def observe(session_id: str, hook_type: str, data: dict, project: str = "", cwd: str = "") -> bool:
    """Envía una observación al backend. Nunca lanza: fail-open por diseño."""
    try:
        secret = resolve_secret()
        body = json.dumps({
            "hookType": hook_type,
            "sessionId": session_id or "unknown",
            "project": project,
            "cwd": cwd,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": _trim(data),
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if secret:
            headers["Authorization"] = f"Bearer {secret}"
        request = urllib.request.Request(
            f"{backend_url()}/agentmemory/observe",
            data=body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            return 200 <= response.status < 300
    except Exception as exc:  # noqa: BLE001 — un hook jamás debe romper el turno
        logger.debug("agentmemory-capture: POST /observe falló: %s", exc)
        return False

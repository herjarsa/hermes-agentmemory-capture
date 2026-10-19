"""Shim para instalación como plugin de directorio Hermes.

Carga el paquete desde `src/` de este mismo repo, sin necesidad de
`pip install`, para que `hermes plugins install <git-url>` funcione
standalone. Instalado vía pip (PyPI), Hermes descubre el paquete por el
entry point `hermes_agent.plugins` y este shim no se usa.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from hermes_agentmemory_capture import HOOKS, register  # noqa: E402,F401

__all__ = ["register", "HOOKS"]

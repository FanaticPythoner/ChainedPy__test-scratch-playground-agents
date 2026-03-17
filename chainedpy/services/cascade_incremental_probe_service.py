from __future__ import annotations

from pathlib import Path


class IncrementalProbe:
    def __init__(self, root: str) -> None:
        self.root = Path(root)

    def build_probe_marker(self, name: str) -> str:
        return f"{self.root.name}:{name}"


def compose_incremental_probe_marker(root: str, name: str) -> str:
    return IncrementalProbe(root).build_probe_marker(name)

"""File operation tools — evolvable implementations.

These tools are simple pure functions decorated with ``@tool``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from palimpsest.runtime.tools import tool, ToolResult


@tool
def read_file(path: str, workspace: str) -> ToolResult:
    """Read the contents of a file in the workspace."""
    target = Path(workspace) / path
    if not target.exists():
        return ToolResult(success=False, output=f"File not found: {path}")
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        if len(content) > 8192:
            content = content[:8192] + f"\n... (truncated, {len(content)} chars total)"
        return ToolResult(success=True, output=content)
    except Exception as exc:
        return ToolResult(success=False, output=f"Error reading file: {exc}")


@tool
def write_file(path: str, content: str, workspace: str) -> ToolResult:
    """Write content to a file in the workspace (creates parent directories if needed)."""
    target = Path(workspace) / path
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult(success=True, output=f"Written {len(content)} chars to {path}")
    except Exception as exc:
        return ToolResult(success=False, output=f"Error writing file: {exc}")


@tool
def list_files(path: str = ".", workspace: str = "") -> ToolResult:
    """List files and directories in the workspace. Returns a tree-like listing."""
    target = Path(workspace) / path
    if not target.exists():
        return ToolResult(success=False, output=f"Directory not found: {path}")
    if not target.is_dir():
        return ToolResult(success=False, output=f"Not a directory: {path}")

    try:
        entries = []
        for item in sorted(target.iterdir()):
            prefix = "d " if item.is_dir() else "f "
            size = f" ({item.stat().st_size}B)" if item.is_file() else ""
            entries.append(f"{prefix}{item.name}{size}")
        return ToolResult(success=True, output="\n".join(entries) if entries else "(empty directory)")
    except Exception as exc:
        return ToolResult(success=False, output=f"Error listing directory: {exc}")

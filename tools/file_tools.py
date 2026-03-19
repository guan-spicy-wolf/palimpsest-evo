"""File operation tools — evolvable implementations.

These tools implement the ``ToolProvider`` interface defined in the
runtime.  They can be freely modified/extended without touching
runtime code.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from palimpsest.runtime.interfaces import ToolProvider, ToolSpec


class ReadFileTool(ToolProvider):
    """Read the contents of a file in the workspace."""

    def tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="read_file",
                description="Read the contents of a file in the workspace.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path relative to workspace root",
                        },
                    },
                    "required": ["path"],
                },
            )
        ]

    def execute(self, name: str, args: dict, workspace: str):
        from palimpsest.gateway.tools import ToolResult

        path = Path(workspace) / args["path"]
        if not path.exists():
            return ToolResult(success=False, output=f"File not found: {args['path']}")
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            # Truncate very large files
            if len(content) > 8192:
                content = content[:8192] + f"\n... (truncated, {len(content)} chars total)"
            return ToolResult(success=True, output=content)
        except Exception as exc:
            return ToolResult(success=False, output=f"Error reading file: {exc}")


class WriteFileTool(ToolProvider):
    """Write content to a file in the workspace."""

    def tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="write_file",
                description="Write content to a file in the workspace (creates parent directories if needed).",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path relative to workspace root",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file",
                        },
                    },
                    "required": ["path", "content"],
                },
            )
        ]

    def execute(self, name: str, args: dict, workspace: str):
        from palimpsest.gateway.tools import ToolResult

        path = Path(workspace) / args["path"]
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args["content"], encoding="utf-8")
            return ToolResult(success=True, output=f"Written {len(args['content'])} chars to {args['path']}")
        except Exception as exc:
            return ToolResult(success=False, output=f"Error writing file: {exc}")


class ListFilesTool(ToolProvider):
    """List files in a directory within the workspace."""

    def tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="list_files",
                description="List files and directories in the workspace. Returns a tree-like listing.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path relative to workspace root (default: '.')",
                        },
                    },
                },
            )
        ]

    def execute(self, name: str, args: dict, workspace: str):
        from palimpsest.gateway.tools import ToolResult

        rel_path = args.get("path", ".")
        target = Path(workspace) / rel_path
        if not target.exists():
            return ToolResult(success=False, output=f"Directory not found: {rel_path}")
        if not target.is_dir():
            return ToolResult(success=False, output=f"Not a directory: {rel_path}")

        try:
            entries = []
            for item in sorted(target.iterdir()):
                prefix = "d " if item.is_dir() else "f "
                size = f" ({item.stat().st_size}B)" if item.is_file() else ""
                entries.append(f"{prefix}{item.name}{size}")
            return ToolResult(success=True, output="\n".join(entries) if entries else "(empty directory)")
        except Exception as exc:
            return ToolResult(success=False, output=f"Error listing directory: {exc}")

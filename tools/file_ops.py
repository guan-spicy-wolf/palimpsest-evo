"""File operations tool provider (evolvable).

Provides read_file, write_file, list_files. Path traversal prevented
by resolving paths relative to workspace and verifying containment.
"""

from __future__ import annotations

import os
from pathlib import Path

from palimpsest.runtime.interfaces import ToolProvider, ToolSpec
from palimpsest.gateway.tools import ToolResult


def _safe_resolve(workspace: str, rel_path: str) -> Path:
    """Resolve a relative path within workspace, raise on traversal."""
    ws = Path(workspace).resolve()
    target = (ws / rel_path).resolve()
    try:
        target.relative_to(ws)
    except ValueError:
        raise ValueError(f"Path traversal denied: {rel_path}")
    return target


class FileOpsProvider(ToolProvider):

    def tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="read_file",
                description="Read the contents of a file in the workspace.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path relative to workspace root"},
                    },
                    "required": ["path"],
                },
            ),
            ToolSpec(
                name="write_file",
                description="Write content to a file in the workspace (overwrites if exists).",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path relative to workspace root"},
                        "content": {"type": "string", "description": "File content to write"},
                    },
                    "required": ["path", "content"],
                },
            ),
            ToolSpec(
                name="list_files",
                description="List files in a directory within the workspace.",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path relative to workspace root (default: .)"},
                    },
                },
            ),
        ]

    def execute(self, name: str, args: dict, workspace: str) -> ToolResult:
        try:
            if name == "read_file":
                return self._read(args, workspace)
            elif name == "write_file":
                return self._write(args, workspace)
            elif name == "list_files":
                return self._list(args, workspace)
            return ToolResult(success=False, output=f"Unknown tool: {name}")
        except ValueError as exc:
            return ToolResult(success=False, output=str(exc))
        except FileNotFoundError as exc:
            return ToolResult(success=False, output=f"File not found: {exc}")
        except Exception as exc:
            return ToolResult(success=False, output=f"Error: {exc}")

    def _read(self, args: dict, workspace: str) -> ToolResult:
        fpath = _safe_resolve(workspace, args["path"])
        if not fpath.is_file():
            return ToolResult(success=False, output=f"File not found: {args['path']}")
        content = fpath.read_text(errors="replace")
        return ToolResult(success=True, output=content[:8192])

    def _write(self, args: dict, workspace: str) -> ToolResult:
        fpath = _safe_resolve(workspace, args["path"])
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(args["content"])
        return ToolResult(success=True, output=f"Written {len(args['content'])} chars to {args['path']}")

    def _list(self, args: dict, workspace: str) -> ToolResult:
        rel = args.get("path", ".")
        dpath = _safe_resolve(workspace, rel)
        if not dpath.is_dir():
            return ToolResult(success=False, output=f"Not a directory: {rel}")
        entries = sorted(os.listdir(dpath))
        return ToolResult(success=True, output="\n".join(entries))

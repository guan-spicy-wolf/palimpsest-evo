"""File tree context provider (evolvable)."""
from __future__ import annotations
import os
from palimpsest.runtime.interfaces import ContextProvider

class FileTreeProvider(ContextProvider):
    @property
    def section_type(self) -> str:
        return "file_tree"

    def render(self, job_id: str, workspace: str, section_config: dict, runtime_deps=None) -> str:
        max_files = section_config.get("max_files", 50)
        excludes = set(section_config.get("exclude", [".git"]))
        lines: list[str] = []
        count = 0
        for dirpath, dirnames, filenames in os.walk(workspace):
            dirnames[:] = [d for d in dirnames if d not in excludes]
            rel_dir = os.path.relpath(dirpath, workspace)
            prefix = "" if rel_dir == "." else rel_dir + "/"
            for fname in filenames:
                lines.append(prefix + fname)
                count += 1
                if count >= max_files:
                    lines.append(f"... (truncated at {max_files} files)")
                    tree = "\n".join(lines)
                    return f"## Workspace file tree\n```\n{tree}\n```"
        tree = "\n".join(lines) if lines else "(empty)"
        return f"## Workspace file tree\n```\n{tree}\n```"

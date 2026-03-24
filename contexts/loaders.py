"""Built-in context loaders for the Agent.

These are pure functions decorated with ``@context_provider``.
They are dynamically loaded by the runtime's context stage.
"""

from __future__ import annotations

import os
from pathlib import Path

from yoitsu_contracts.client import EventEmitter

from palimpsest.config import JobConfig
from palimpsest.runtime.contexts import context_provider


@context_provider("task_description")
def task_description(task: str, description: str = "Task Description") -> str:
    """Render the primary task description."""
    return f"## {description}\n\n{task}"


@context_provider("file_tree")
def file_tree(
    workspace: str,
    description: str = "Workspace file structure",
    max_files: int = 100,
    exclude: list[str] | None = None,
) -> str:
    """Render a simple file tree of the workspace."""
    if not exclude:
        exclude = [".git", "__pycache__", ".venv"]

    root = Path(workspace)
    lines = [f"## {description}\n", "."]
    
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # Extremely basic tree walk with ignore logic
        dirnames[:] = [d for d in dirnames if d not in exclude and not d.endswith(".egg-info")]
        
        rel_dir = Path(dirpath).relative_to(root)
        if rel_dir.name == "":
            depth = 0
        else:
            depth = len(rel_dir.parts)
            
        indent = "  " * depth
        if depth > 0:
            lines.append(f"{indent}├── {rel_dir.name}/")
            
        for f in filenames:
            if f in exclude or any(f.endswith(ext) for ext in [".pyc", ".o"]):
                continue
            count += 1
            if count > max_files:
                lines.append(f"{indent}  └── ... (truncated at {max_files} files)")
                break
            lines.append(f"{indent}  ├── {f}")
            
        if count > max_files:
            break

    return "\n".join(lines)




@context_provider("version_history")
def version_history(description: str = "Version History", limit: int = 5) -> str:
    # A placeholder implementation. In a real scenario, this might query the Supervisor
    # or the git history of the evo repository.
    return f"## {description}\n\n(Version history tracking currently delegating to supervisor)"


@context_provider("join_context")
def join_context(job_config: JobConfig, description: str = "Join Context") -> str:
    join = job_config.context.join
    if join is None or not join.child_task_ids:
        return ""

    emitter = EventEmitter(job_config.eventstore)
    latest_by_task: dict[str, dict] = {}
    try:
        for event in emitter.fetch_all(type_="task.updated"):
            data = event.data
            task_id = data.get("task_id", "")
            if task_id in join.child_task_ids:
                latest_by_task[task_id] = data
    finally:
        emitter.close()

    lines = [
        f"## {description}",
        "",
        f"Parent job: {join.parent_job_id}",
    ]
    if join.parent_summary:
        lines.extend(["", "### Parent Summary", join.parent_summary])

    lines.extend(["", "### Child Task States"])
    for task_id in join.child_task_ids:
        data = latest_by_task.get(task_id, {})
        status = data.get("status", "unknown")
        summary = data.get("summary", "(no summary yet)")
        lines.append(f"- {task_id}: {status} - {summary}")

    return "\n".join(lines)

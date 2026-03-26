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
from palimpsest.runtime.roles import RoleManager, TeamManager


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
    eval_ctx = job_config.context.eval
    if (join is None or not join.child_task_ids) and eval_ctx is None:
        return ""

    emitter = EventEmitter(job_config.eventstore)
    latest_by_task: dict[str, dict] = {}
    child_task_ids = list(join.child_task_ids if join else eval_ctx.child_task_ids)
    try:
        for ev_type in ("task.completed", "task.failed", "task.partial", "task.cancelled", "task.eval_failed"):
            for event in emitter.fetch_all(type_=ev_type):
                data = dict(event.data)
                task_id = data.get("task_id", "")
                if task_id in child_task_ids:
                    # Determine status from event type suffix
                    data["status"] = "eval_failed" if ev_type == "task.eval_failed" else ev_type.split(".")[1]
                    latest_by_task[task_id] = data
    finally:
        emitter.close()

    lines = [
        f"## {description}",
        "",
        f"Parent job: {(join.parent_job_id if join else '')}",
    ]
    if join and join.parent_summary:
        lines.extend(["", "### Parent Summary", join.parent_summary])
    if eval_ctx is not None:
        if eval_ctx.goal:
            lines.extend(["", "### Eval Goal", eval_ctx.goal])
        if eval_ctx.deliverables:
            lines.extend(["", "### Expected Deliverables"])
            for item in eval_ctx.deliverables:
                lines.append(f"- {item}")
        if eval_ctx.criteria:
            lines.extend(["", "### Verification Criteria"])
            for item in eval_ctx.criteria:
                lines.append(f"- {item}")
        if eval_ctx.structural:
            lines.extend(["", "### Structural Verdict Snapshot", str(eval_ctx.structural)])

    lines.extend(["", "### Child Task States"])
    for task_id in child_task_ids:
        data = latest_by_task.get(task_id, {})
        status = data.get("status", "unknown")
        summary = data.get("summary") or data.get("reason") or "(no summary yet)"
        lines.append(f"- {task_id}: {status} - {summary}")
        result = data.get("result")
        if isinstance(result, dict):
            semantic = (result.get("semantic") or {}).get("verdict", "unknown")
            structural = result.get("structural") or {}
            lines.append(f"  semantic={semantic}, structural={structural}")

    return "\n".join(lines)


@context_provider("available_roles")
def available_roles(
    evo_root: str,
    job_config: JobConfig,
    description: str = "Available Roles",
) -> str:
    team_manager = TeamManager(evo_root)
    role_manager = RoleManager(evo_root)
    team = team_manager.resolve(job_config.team or "default")

    lines = [
        f"## {description}",
        "",
        f"Team: {team.name}",
        team.description,
    ]
    for role_name in team.roles:
        role = role_manager._load_role(role_name)
        tools = ", ".join(role.tools) if role.tools else "(no evo tools)"
        lines.extend(
            [
                "",
                f"### {role.name}",
                role.description,
                f"Tools: {tools}",
            ]
        )
    return "\n".join(lines)


@context_provider("eval_context")
def eval_context(job_config: JobConfig, description: str = "Evaluation Context") -> str:
    eval_cfg = job_config.context.eval
    if eval_cfg is None:
        return ""

    lines = [f"## {description}"]
    if eval_cfg.goal:
        lines.extend(["", "### Goal", eval_cfg.goal])
    if eval_cfg.deliverables:
        lines.extend(["", "### Deliverables"])
        for item in eval_cfg.deliverables:
            lines.append(f"- {item}")
    if eval_cfg.criteria:
        lines.extend(["", "### Verification Criteria"])
        for item in eval_cfg.criteria:
            lines.append(f"- {item}")
    if eval_cfg.structural:
        lines.extend(["", "### Structural Verdict", str(eval_cfg.structural)])
    if eval_cfg.child_task_ids:
        lines.extend(["", "### Child Tasks"])
        for task_id in eval_cfg.child_task_ids:
            lines.append(f"- {task_id}")
    return "\n".join(lines)


@context_provider("job_trace")
def job_trace(job_config: JobConfig, description: str = "Job Execution Trace") -> str:
    eval_cfg = job_config.context.eval
    task_id = eval_cfg.task_id if eval_cfg is not None else job_config.task_id
    if not task_id:
        return ""

    emitter = EventEmitter(job_config.eventstore)
    trace_rows: list[tuple[str, str, str, str, str]] = []
    try:
        launched_by_job: dict[str, dict] = {}
        for event in emitter.fetch_all(type_="supervisor.job.launched"):
            data = dict(event.data)
            job_id = data.get("job_id", "")
            if job_id and data.get("task_id", "") == task_id:
                launched_by_job[job_id] = data

        for ev_type in ("job.completed", "job.failed", "job.cancelled"):
            for event in emitter.fetch_all(type_=ev_type):
                data = dict(event.data)
                job_id = data.get("job_id", "")
                if not job_id or data.get("task_id", "") != task_id:
                    continue
                launch = launched_by_job.get(job_id, {})
                summary = (
                    str(data.get("summary") or data.get("error") or data.get("reason") or "").strip()
                    or "(no summary)"
                )
                trace_rows.append(
                    (
                        job_id,
                        str(launch.get("role", "")),
                        ev_type.split(".")[1],
                        summary,
                        str(data.get("git_ref") or ""),
                    )
                )
    finally:
        emitter.close()

    lines = [f"## {description}"]
    if not trace_rows:
        lines.extend(["", "(No completed job trace available yet)"])
        return "\n".join(lines)

    for job_id, role, status, summary, git_ref in trace_rows:
        lines.extend(
            [
                "",
                f"- {job_id}",
                f"  role={role or 'unknown'} status={status}",
                f"  summary={summary}",
                f"  git_ref={git_ref or '(none)'}",
            ]
        )
    return "\n".join(lines)

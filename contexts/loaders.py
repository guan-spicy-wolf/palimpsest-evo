"""Built-in context loaders for the Agent.

These are pure functions decorated with ``@context_provider``.
They are dynamically loaded by the runtime's context stage.
"""

from __future__ import annotations

import os
import httpx
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from yoitsu_contracts.client import EventEmitter
from yoitsu_contracts.env import api_key_headers

from palimpsest.config import JobConfig
from palimpsest.runtime.contexts import context_provider
from palimpsest.runtime.roles import RoleManager, TeamManager


def _latest_child_task_states(job_config: JobConfig, child_task_ids: list[str]) -> dict[str, dict]:
    if not child_task_ids:
        return {}

    emitter = EventEmitter(job_config.eventstore)
    latest_by_task: dict[str, dict] = {}
    launched_by_job: dict[str, dict] = {}
    try:
        for event in emitter.fetch_all(type_="supervisor.job.launched"):
            data = dict(event.data)
            task_id = data.get("task_id", "")
            job_id = data.get("job_id", "")
            if task_id in child_task_ids and job_id:
                launched_by_job[job_id] = data

        for ev_type in ("supervisor.task.completed", "supervisor.task.failed", "supervisor.task.partial", "supervisor.task.cancelled", "supervisor.task.eval_failed"):
            for event in emitter.fetch_all(type_=ev_type):
                data = dict(event.data)
                task_id = data.get("task_id", "")
                if task_id in child_task_ids:
                    data["status"] = "eval_failed" if ev_type == "supervisor.task.eval_failed" else ev_type.split(".")[2]
                    result = data.get("result")
                    if isinstance(result, dict):
                        trace = result.get("trace")
                        if isinstance(trace, list):
                            enriched_trace = []
                            for entry in trace:
                                if not isinstance(entry, dict):
                                    enriched_trace.append(entry)
                                    continue
                                launch = launched_by_job.get(str(entry.get("job_id", "")), {})
                                merged = dict(entry)
                                if launch.get("repo") and not merged.get("repo"):
                                    merged["repo"] = launch["repo"]
                                init_branch = str(launch.get("init_branch", "") or "")
                                if init_branch and not merged.get("base_branch"):
                                    merged["base_branch"] = init_branch
                                enriched_trace.append(merged)
                            result["trace"] = enriched_trace
                    latest_by_task[task_id] = data
    finally:
        emitter.close()
    return latest_by_task


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

    child_task_ids = list(join.child_task_ids if join else eval_ctx.child_task_ids)
    latest_by_task = _latest_child_task_states(job_config, child_task_ids)

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
            semantic_summary = (result.get("semantic") or {}).get("summary", "")
            criteria_results = (result.get("semantic") or {}).get("criteria_results") or []
            structural = result.get("structural") or {}
            lines.append(f"  semantic={semantic}, structural={structural}")
            if semantic_summary:
                lines.append(f"  semantic_summary={semantic_summary}")
            if criteria_results:
                lines.append(f"  criteria_results={criteria_results}")
            trace = result.get("trace") or []
            publication_target = next(
                (
                    entry
                    for entry in trace
                    if isinstance(entry, dict) and entry.get("git_ref") and entry.get("repo")
                ),
                None,
            )
            if isinstance(publication_target, dict):
                git_ref = str(publication_target.get("git_ref", "") or "")
                head_branch = git_ref.split(":", 1)[0].strip() if ":" in git_ref else ""
                lines.append(
                    "  publication_target: "
                    f"repo={publication_target.get('repo', '') or '(none)'} "
                    f"base_branch={publication_target.get('base_branch', '') or '(none)'} "
                    f"head_branch={head_branch or '(none)'}"
                )
            if trace:
                for entry in trace:
                    if not isinstance(entry, dict):
                        continue
                    lines.append(
                        "  trace: "
                        f"job_id={entry.get('job_id', '')} "
                        f"role={entry.get('role', '') or 'unknown'} "
                        f"outcome={entry.get('outcome', '') or 'unknown'} "
                        f"repo={entry.get('repo', '') or '(none)'} "
                        f"base_branch={entry.get('base_branch', '') or '(none)'} "
                        f"git_ref={entry.get('git_ref', '') or '(none)'} "
                        f"summary={entry.get('summary', '') or '(no summary)'}"
                    )

    return "\n".join(lines)


@context_provider("available_roles")
def available_roles(
    evo_root: str,
    job_config: JobConfig,
    description: str = "Available Roles",
) -> str:
    """Render available roles for the job's team.
    
    Per ADR-0011: Uses team-aware RoleManager for directory-based resolution.
    """
    team_name = job_config.team or "default"
    team_manager = TeamManager(evo_root, team=team_name)
    role_manager = RoleManager(evo_root, team=team_name)
    team = team_manager.resolve(team_name)

    lines = [
        f"## {description}",
        "",
        f"Team: {team.name}",
        team.description,
    ]
    worker_roles = list(getattr(team, "worker_roles", getattr(team, "roles", [])))
    for role_name in worker_roles:
        try:
            role = role_manager.get_definition(role_name)
            spec = role_manager.resolve(role_name)
        except Exception as exc:
            lines.extend(
                [
                    "",
                    f"### {role_name}",
                    f"[Unavailable role definition: {exc}]",
                ]
            )
            continue

        tools = ", ".join(spec.tools) if spec.tools else "(no evo tools)"
        lines.extend(
            [
                "",
                f"### {role.name}",
                role.description,
                f"Capability: {role.min_capability or '(unspecified)'}",
                f"Budget: min={role.min_cost:.2f}, recommended={role.recommended_cost:.2f}",
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
        latest_by_task = _latest_child_task_states(job_config, eval_cfg.child_task_ids)
        for task_id in eval_cfg.child_task_ids:
            data = latest_by_task.get(task_id, {})
            status = data.get("status", "unknown")
            summary = data.get("summary") or data.get("reason") or "(no summary yet)"
            lines.append(f"- {task_id}: {status} - {summary}")
        lines.extend(
            [
                "",
                "Use `join_context` for the fuller child-state breakdown, including structural and semantic details.",
            ]
        )
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

        for ev_type in ("agent.job.completed", "agent.job.failed", "agent.job.cancelled"):
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


@context_provider("github_context")
def github_context(
    job_config: JobConfig,
    description: str = "GitHub Context",
) -> str:
    """Render GitHub PR/Issue context for reviewer role.

    This context provider reads GitHub context from job_config.params
    and formats it for the LLM to understand what it's reviewing.

    The GitHub context is populated when external events (PR labeled,
    Issue labeled) trigger tasks.
    """
    params = job_config.role_params or {}
    github_data = params.get("github_context", {})

    if not github_data:
        return ""

    lines = [f"## {description}", ""]

    # PR context
    pr = github_data.get("pr")
    if pr:
        lines.append("### Pull Request")
        lines.append(f"- **Number**: #{pr.get('number', '?')}")
        lines.append(f"- **URL**: {pr.get('url', '(unknown)')}")
        lines.append(f"- **Title**: {pr.get('title', '(no title)')}")
        lines.append(f"- **Author**: {pr.get('author', '(unknown)')}")
        lines.append(f"- **Branch**: {pr.get('head_branch', '?')} -> {pr.get('base_branch', 'main')}")
        lines.append(f"- **State**: {pr.get('state', 'open')}")
        
        files = pr.get("files", [])
        if files:
            lines.append(f"- **Changed Files** ({len(files)}):")
            for f in files[:20]:  # Limit to 20 files
                lines.append(f"  - {f}")
            if len(files) > 20:
                lines.append(f"  - ... and {len(files) - 20} more")
        
        body = pr.get("body", "")
        if body:
            lines.append("")
            lines.append("**PR Description:**")
            lines.append(body)

        comments = pr.get("comments", [])
        if comments:
            lines.append("")
            lines.append(f"**Comments** ({len(comments)}):")
            for c in comments[:10]:  # Limit to 10 comments
                author = c.get("author", "?")
                body_preview = c.get("body", "")[:200]
                lines.append(f"- @{author}: {body_preview}")

    # Issue context
    issue = github_data.get("issue")
    if issue:
        lines.append("")
        lines.append("### Issue")
        lines.append(f"- **Number**: #{issue.get('number', '?')}")
        lines.append(f"- **URL**: {issue.get('url', '(unknown)')}")
        lines.append(f"- **Title**: {issue.get('title', '(no title)')}")
        lines.append(f"- **Author**: {issue.get('author', '(unknown)')}")
        lines.append(f"- **State**: {issue.get('state', 'open')}")
        
        labels = issue.get("labels", [])
        if labels:
            lines.append(f"- **Labels**: {', '.join(labels)}")
        
        body = issue.get("body", "")
        if body:
            lines.append("")
            lines.append("**Issue Description:**")
            lines.append(body)

        comments = issue.get("comments", [])
        if comments:
            lines.append("")
            lines.append(f"**Comments** ({len(comments)}):")
            for c in comments[:10]:
                author = c.get("author", "?")
                body_preview = c.get("body", "")[:200]
                lines.append(f"- @{author}: {body_preview}")

    return "\n".join(lines) if len(lines) > 2 else ""


@context_provider("observation_context")
def observation_context(
    job_config: JobConfig,
    description: str = "Observation Context",
    window_hours: int = 24,
    metric_type: str | None = None,
    role: str | None = None,
) -> str:
    """Render observation aggregation for self-optimization review.

    This context provider queries Pasloe observation endpoints to provide
    budget variance statistics.

    Per ADR-0010: observation signals enable Review Task to identify
    optimization targets with structured data and causal chain.

    Args:
        job_config: Job configuration with eventstore settings
        description: Section header for context
        window_hours: Time window for aggregation (from trigger params)
        metric_type: Filter by metric type (budget_variance, preparation_failure, tool_retry)
        role: Filter by role (from trigger params)
    """
    eventstore = job_config.eventstore
    if not eventstore.url:
        return ""

    lines = [f"## {description}", "", f"Time window: last {window_hours} hours"]
    if metric_type:
        lines.append(f"Metric filter: {metric_type}")
    if role:
        lines.append(f"Role filter: {role}")

    # Query observation endpoints
    headers = api_key_headers(eventstore.api_key_env) if eventstore.api_key_env else {}
    client = httpx.Client(
        base_url=eventstore.url.rstrip("/"),
        headers=headers,
        timeout=10.0,
    )

    try:
        # Route based on metric_type (per ADR-0010)
        # Only budget_variance endpoints exist in Pasloe currently
        if metric_type is None or metric_type == "budget_variance":
            # Budget variance aggregation (with optional role filter)
            agg_params = {"window_hours": window_hours}
            if role:
                agg_params["role"] = role

            resp = client.get("/observation/budget_variance/aggregate", params=agg_params)
            if resp.status_code == 200:
                agg = resp.json()
                lines.extend([
                    "",
                    "### Budget Variance Analysis",
                    f"- Sample count: {agg.get('sample_count', 0)}",
                    f"- Mean variance ratio: {agg.get('mean_variance_ratio', 0.0):.3f}",
                    f"- Median variance ratio: {agg.get('median_variance_ratio', 0.0):.3f}",
                    f"- Underestimate rate: {agg.get('underestimate_rate', 0.0):.1%}",
                    f"- Overestimate rate: {agg.get('overestimate_rate', 0.0):.1%}",
                    f"- Total estimated budget: {agg.get('total_estimated_budget', 0.0):.2f}",
                    f"- Total actual cost: {agg.get('total_actual_cost', 0.0):.2f}",
                ])

                # Per-role breakdown (skip if we filtered by a specific role)
                if not role:
                    resp_roles = client.get("/observation/budget_variance/by_role", params={"window_hours": window_hours})
                    if resp_roles.status_code == 200:
                        role_stats = resp_roles.json()
                        if role_stats:
                            lines.extend(["", "#### By Role"])
                            for rs in role_stats:
                                lines.append(
                                    f"- {rs.get('role', 'unknown')}: "
                                    f"n={rs.get('sample_count', 0)}, "
                                    f"mean_var={rs.get('mean_variance_ratio', 0.0):.3f}, "
                                    f"est={rs.get('total_estimated_budget', 0.0):.2f}, "
                                    f"actual={rs.get('total_actual_cost', 0.0):.2f}"
                                )
        elif metric_type in ("preparation_failure", "tool_retry"):
            # Endpoints not yet implemented in Pasloe
            # Per ADR-0010: these are advertised but routes don't exist yet
            lines.extend([
                "",
                f"### {metric_type.replace('_', ' ').title()} Analysis",
                "No data available: endpoint not yet implemented.",
                "",
                f"The {metric_type} metric type is recognized but Pasloe does not yet ",
                "expose aggregation endpoints for this metric.",
            ])
        else:
            # Unknown metric type - fail explicitly rather than silently
            lines.extend([
                "",
                f"### Unknown Metric Type: {metric_type}",
                f"WARNING: '{metric_type}' is not a recognized metric type.",
                "",
                "Supported metric types are:",
                "- budget_variance (default)",
                "- preparation_failure (endpoint not yet implemented)",
                "- tool_retry (endpoint not yet implemented)",
                "",
                "No observation data loaded.",
            ])

    except httpx.HTTPError as exc:
        lines.extend(["", f"[Error querying observation data: {exc}]"])
    finally:
        client.close()

    return "\n".join(lines) if len(lines) > 2 else ""

"""Optimizer role for self-optimization governance (ADR-0010).

This role is distinct from the code reviewer role:
- optimizer: Reviews system observations and produces optimization proposals
- reviewer: Reviews PR/Issue content and provides code review feedback

Per ADR-0010: The optimizer consumes structured observation signals (budget variance,
preparation failures, tool retry patterns) and outputs actionable proposals that
can be converted into optimization tasks.
"""
from palimpsest.runtime import JobSpec, context_spec, git_publication, role, workspace_config


@role(
    name="optimizer",
    description="Reviews system observations and produces optimization proposals (ADR-0010)",
    teams=["default", "backend"],
    role_type="worker",
    min_cost=0.08,
    recommended_cost=0.40,
    max_cost=1.00,  # ADR-0004 D1a
    min_capability="reasoning_medium",
)
def optimizer_role(**params) -> JobSpec:
    # Extract observation context params from trigger (ADR-0010)
    # observation_threshold trigger passes: metric_type, threshold, current_value,
    # trigger_role, window_hours
    observation_context_config = {
        "type": "observation_context",
        "window_hours": params.get("window_hours", 24),
    }
    # Pass through metric filters if available
    if params.get("metric_type"):
        observation_context_config["metric_type"] = params["metric_type"]
    if params.get("trigger_role"):
        observation_context_config["role"] = params["trigger_role"]

    return JobSpec(
        preparation_fn=workspace_config(),
        context_fn=context_spec(
            "prompts/optimizer.md",
            [
                observation_context_config,  # ADR-0010 observation signals (from trigger)
                {"type": "task_description"},
                {"type": "join_context"},
                {"type": "file_tree", "max_files": 150, "exclude": [".git", "__pycache__", ".venv"]},
                {"type": "version_history", "limit": 10},
            ],
        ),
        publication_fn=git_publication(),
        tools=[
            "read_file",
            "list_files",
        ],
    )
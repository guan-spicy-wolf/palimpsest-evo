from palimpsest.runtime import JobSpec, context_spec, git_publication, role, workspace_config


def _planner_context(mode: str):
    if mode == "join":
        return context_spec(
            "prompts/planner-join.md",
            [
                {"type": "task_description"},
                {"type": "join_context"},
                {"type": "available_roles"},
                {"type": "job_trace"},
            ],
        )
    return context_spec(
        "prompts/planner.md",
        [
            {"type": "task_description"},
            {"type": "available_roles"},
            {"type": "file_tree", "max_files": 200, "exclude": [".git", "__pycache__", ".venv"]},
            {"type": "version_history", "limit": 10},
        ],
    )


@role(
    name="planner",
    description="Decomposes goals into concrete subtasks with deliverables and verification criteria",
    teams=["default", "backend"],
    role_type="planner",
    min_cost=0.10,
    recommended_cost=0.40,
    max_cost=0.50,  # ADR-0004 D1a: conservative ceiling for planning
    min_capability="reasoning_medium",
)
def planner_role(**params) -> JobSpec:
    mode = str(params.get("mode") or "initial")
    return JobSpec(
        preparation_fn=workspace_config(new_branch=False),
        context_fn=_planner_context(mode),
        publication_fn=git_publication(strategy="skip"),
        tools=[
            "spawn",
            "create_pr",
            "read_file",
            "list_files",
        ],
    )

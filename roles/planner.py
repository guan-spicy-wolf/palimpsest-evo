from palimpsest.runtime import JobSpec, context_spec, git_publication, role, workspace_config


@role(
    name="planner",
    description="Decomposes goals into concrete subtasks with deliverables and verification criteria",
    teams=["default", "backend"],
    role_type="planner",
    min_cost=0.10,
    recommended_cost=0.40,
    min_capability="reasoning_medium",
)
def planner_role() -> JobSpec:
    return JobSpec(
        workspace_fn=workspace_config(new_branch=False),
        context_fn=context_spec(
            "prompts/planner.md",
            [
                {"type": "task_description"},
                {"type": "available_roles"},
                {"type": "file_tree", "max_files": 200, "exclude": [".git", "__pycache__", ".venv"]},
                {"type": "version_history", "limit": 10},
            ],
        ),
        publication_fn=git_publication(strategy="skip"),
        tools=[
            "read_file",
            "list_files",
        ],
    )

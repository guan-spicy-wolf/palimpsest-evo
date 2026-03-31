from palimpsest.runtime import JobSpec, context_spec, git_publication, role, workspace_config


@role(
    name="default",
    description="General-purpose coding role for straightforward implementation tasks",
    teams=["default"],
    role_type="worker",
    min_cost=0.05,
    recommended_cost=0.30,
    max_cost=2.00,  # ADR-0004 D1a
    min_capability="reasoning_medium",
)
def default_role(**params) -> JobSpec:
    return JobSpec(
        preparation_fn=workspace_config(),
        context_fn=context_spec(
            "prompts/default.md",
            [
                {"type": "task_description"},
                {"type": "join_context"},
                {"type": "file_tree", "max_files": 100, "exclude": [".git", "__pycache__", ".venv"]},
                {"type": "version_history", "limit": 5},
            ],
        ),
        publication_fn=git_publication(),
        tools=[
            "read_file",
            "write_file",
            "list_files",
        ],
    )

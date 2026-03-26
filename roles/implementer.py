from palimpsest.runtime import JobSpec, role


@role(
    name="implementer",
    description="Implements code changes and tests for a scoped engineering task",
    teams=["default", "backend"],
    role_type="worker",
    min_cost=0.10,
    recommended_cost=0.80,
    min_capability="reasoning_medium",
)
def implementer_role() -> JobSpec:
    return JobSpec(
        prompt="prompts/default.md",
        context_template={
            "sections": [
                {"type": "task_description"},
                {"type": "join_context"},
                {"type": "file_tree", "max_files": 150, "exclude": [".git", "__pycache__", ".venv"]},
                {"type": "version_history", "limit": 10},
            ]
        },
        tools=[
            "read_file",
            "write_file",
            "list_files",
        ],
    )

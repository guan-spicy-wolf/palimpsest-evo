from palimpsest.runtime import JobSpec, role


@role(
    name="default",
    description="General-purpose coding role for straightforward implementation tasks",
    teams=["default"],
    role_type="worker",
    min_cost=0.05,
    recommended_cost=0.30,
    min_capability="reasoning_medium",
)
def default_role() -> JobSpec:
    return JobSpec(
        prompt="prompts/default.md",
        context_template={
            "sections": [
                {"type": "task_description"},
                {"type": "join_context"},
                {"type": "file_tree", "max_files": 100, "exclude": [".git", "__pycache__", ".venv"]},
                {"type": "version_history", "limit": 5},
            ]
        },
        tools=[
            "read_file",
            "write_file",
            "list_files",
        ],
    )

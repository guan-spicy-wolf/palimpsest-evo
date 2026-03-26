from palimpsest.runtime import JobSpec, role


@role(
    name="reviewer",
    description="Reviews task outputs against requirements and highlights gaps or risks",
    teams=["default", "backend"],
    role_type="worker",
    min_cost=0.08,
    recommended_cost=0.40,
    min_capability="reasoning_medium",
)
def reviewer_role() -> JobSpec:
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
            "list_files",
        ],
    )

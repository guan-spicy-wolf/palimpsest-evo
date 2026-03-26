from palimpsest.runtime import JobSpec, role


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
        prompt="prompts/planner.md",
        context_template={
            "sections": [
                {"type": "task_description"},
                {"type": "available_roles"},
                {"type": "file_tree", "max_files": 200, "exclude": [".git", "__pycache__", ".venv"]},
                {"type": "version_history", "limit": 10},
            ]
        },
        tools=[
            "read_file",
            "list_files",
        ],
    )

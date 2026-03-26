from palimpsest.runtime import RoleDefinition

role = RoleDefinition(
    name="planner",
    description="Decomposes goals into concrete subtasks with deliverables and verification criteria",
    prompt="prompts/planner.md",
    contexts=[
        {"type": "task_description"},
        {"type": "available_roles"},
        {"type": "file_tree", "max_files": 200, "exclude": [".git", "__pycache__", ".venv"]},
        {"type": "version_history", "limit": 10},
    ],
    tools=[
        "read_file",
        "list_files",
    ],
)

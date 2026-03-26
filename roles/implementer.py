from palimpsest.runtime import RoleDefinition

role = RoleDefinition(
    name="implementer",
    description="Implements code changes and tests for a scoped engineering task",
    prompt="prompts/default.md",
    contexts=[
        {"type": "task_description"},
        {"type": "join_context"},
        {"type": "file_tree", "max_files": 150, "exclude": [".git", "__pycache__", ".venv"]},
        {"type": "version_history", "limit": 10},
    ],
    tools=[
        "read_file",
        "write_file",
        "list_files",
    ],
)

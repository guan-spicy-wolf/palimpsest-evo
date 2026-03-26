from palimpsest.runtime import RoleDefinition

role = RoleDefinition(
    name="reviewer",
    description="Reviews task outputs against requirements and highlights gaps or risks",
    prompt="prompts/default.md",
    contexts=[
        {"type": "task_description"},
        {"type": "join_context"},
        {"type": "file_tree", "max_files": 150, "exclude": [".git", "__pycache__", ".venv"]},
        {"type": "version_history", "limit": 10},
    ],
    tools=[
        "read_file",
        "list_files",
    ],
)

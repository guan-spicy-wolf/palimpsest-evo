"""Default Agent Role defined in Python.

This structure eliminates YAML mapping errors and leverages Python natively.
"""

from palimpsest.runtime import RoleDefinition

role = RoleDefinition(
    name="default",
    prompt="prompts/default.md",
    contexts=[
        {"type": "task_description"},
        {"type": "file_tree", "max_files": 100, "exclude": [".git", "__pycache__", ".venv", "*.pyc"]},
        {"type": "version_history", "limit": 5},
    ],
    tools=[
        "read_file",
        "write_file",
        "list_files",
    ]
)

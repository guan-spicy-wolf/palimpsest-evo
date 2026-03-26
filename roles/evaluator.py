from palimpsest.runtime import RoleDefinition

role = RoleDefinition(
    name="evaluator",
    description="Assesses task outputs against deliverables and verification criteria",
    prompt="prompts/evaluator.md",
    contexts=[
        {"type": "task_description"},
        {"type": "eval_context"},
        {"type": "job_trace"},
        {"type": "join_context"},
        {"type": "file_tree", "max_files": 200, "exclude": [".git", "__pycache__", ".venv", "*.pyc"]},
    ],
    tools=[
        "read_file",
        "list_files",
    ],
)

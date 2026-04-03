from palimpsest.runtime import JobSpec, context_spec, git_publication, role, workspace_config


@role(
    name="reviewer",
    description="Reviews task outputs against requirements and highlights gaps or risks",
    teams=["default", "backend"],
    role_type="worker",
    min_cost=0.08,
    recommended_cost=0.40,
    max_cost=1.00,  # ADR-0004 D1a
    min_capability="reasoning_medium",
)
def reviewer_role(**params) -> JobSpec:
    """Review role for GitHub PR/Issue code review.

    This role is for reviewing code changes and providing feedback.
    For observation-based optimization proposals, use the optimizer role.
    """
    return JobSpec(
        preparation_fn=workspace_config(),
        context_fn=context_spec(
            "prompts/default.md",
            [
                {"type": "github_context"},  # GitHub PR/Issue context (if available)
                {"type": "task_description"},
                {"type": "join_context"},
                {"type": "file_tree", "max_files": 150, "exclude": [".git", "__pycache__", ".venv"]},
                {"type": "version_history", "limit": 10},
            ],
        ),
        publication_fn=git_publication(),
        tools=[
            "read_file",
            "list_files",
        ],
    )

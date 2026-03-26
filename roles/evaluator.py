from palimpsest.runtime import JobSpec, role


@role(
    name="evaluator",
    description="Assesses task outputs against deliverables and verification criteria",
    teams=["default", "backend"],
    role_type="evaluator",
    min_cost=0.08,
    recommended_cost=0.30,
    min_capability="reasoning_medium",
)
def evaluator_role() -> JobSpec:
    return JobSpec(
        prompt="prompts/evaluator.md",
        context_template={
            "sections": [
                {"type": "task_description"},
                {"type": "eval_context"},
                {"type": "job_trace"},
                {"type": "join_context"},
                {"type": "file_tree", "max_files": 200, "exclude": [".git", "__pycache__", ".venv"]},
            ]
        },
        tools=[
            "read_file",
            "list_files",
        ],
    )

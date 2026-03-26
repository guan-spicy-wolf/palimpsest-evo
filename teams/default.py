from palimpsest.runtime import TeamDefinition

team = TeamDefinition(
    name="default",
    description="General planning and implementation team",
    roles=["default", "implementer", "reviewer"],
    planner_role="planner",
    eval_role="evaluator",
)

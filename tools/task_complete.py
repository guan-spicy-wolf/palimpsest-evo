"""Task completion signal provider (evolvable).

Returns a ToolResult with terminal=True. The runtime's interaction loop
checks this flag and ends the loop.
"""

from __future__ import annotations

from palimpsest.runtime.interfaces import ToolProvider, ToolSpec
from palimpsest.gateway.tools import ToolResult


class TaskCompleteProvider(ToolProvider):

    def tools(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name="task_complete",
                description="Signal that the task is complete. Provide a summary and status.",
                parameters={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Brief summary of what was accomplished"},
                        "status": {
                            "type": "string",
                            "enum": ["success", "partial"],
                            "description": "Whether the task was fully or partially completed",
                        },
                    },
                    "required": ["summary", "status"],
                },
            ),
        ]

    def execute(self, name: str, args: dict, workspace: str) -> ToolResult:
        summary = args.get("summary", "")
        status = args.get("status", "success")
        return ToolResult(
            success=True,
            output=f"[{status}] {summary}",
            terminal=True,
        )

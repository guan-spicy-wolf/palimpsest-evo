"""Task completion signal provider (evolvable).

Returns a ToolResult with terminal=True. The runtime's interaction loop
checks this flag and ends the loop.
"""

from __future__ import annotations

from palimpsest.runtime.tools import tool, ToolResult


@tool
def task_complete(summary: str, status: str = "success") -> ToolResult:
    """Signal that the task is complete. Provide a summary and status.

    Args:
        summary: Brief summary of what was accomplished.
        status: Whether the task was fully or partially completed ('success' or 'partial').
    """
    return ToolResult(
        success=True,
        output=f"[{status}] {summary}",
        terminal=True,
    )

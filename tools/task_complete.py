"""Task completion signal provider (evolvable).

Returns a ToolResult with terminal=True. The runtime's interaction loop
checks this flag and ends the loop.
"""

from __future__ import annotations

from palimpsest.runtime.tools import tool, ToolResult


@tool
def task_complete(summary: str, status: str = "complete") -> ToolResult:
    """Signal that the task is complete. Provide a summary and status.

    Args:
        summary: Brief summary of what was accomplished.
        status: One of complete, failed, in_progress, blocked, needs_review.
    """
    return ToolResult(
        success=True,
        output=f"[{status}] {summary}",
        terminal=True,
    )

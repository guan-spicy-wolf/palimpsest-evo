"""Task completion signal provider (evolvable).

Returns a ToolResult with terminal=True. The runtime's interaction loop
checks this flag and ends the loop.
"""

from __future__ import annotations

from palimpsest.runtime.tools import tool, ToolResult


@tool
def task_complete(summary: str) -> ToolResult:
    """Signal that your work on exactly this job is complete, providing a summary.
    
    This will end your current interaction loop.

    Args:
        summary: Brief summary of what was accomplished in this job.
    """
    return ToolResult(
        success=True,
        output=f"[complete] {summary}",
        terminal=True,
    )

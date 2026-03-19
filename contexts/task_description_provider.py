"""Task description context provider (evolvable). Requires runtime_deps["task"]."""
from __future__ import annotations
from palimpsest.runtime.interfaces import ContextProvider

class TaskDescriptionProvider(ContextProvider):
    @property
    def section_type(self) -> str:
        return "task_description"

    def render(self, job_id: str, workspace: str, section_config: dict, runtime_deps=None) -> str:
        task = (runtime_deps or {}).get("task", "(no task provided)")
        return f"## Task\n{task}"

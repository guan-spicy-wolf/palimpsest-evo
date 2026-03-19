"""Version history context provider (evolvable). Currently degraded placeholder."""
from __future__ import annotations
from palimpsest.runtime.interfaces import ContextProvider

class VersionHistoryProvider(ContextProvider):
    @property
    def section_type(self) -> str:
        return "version_history"

    def render(self, job_id: str, workspace: str, section_config: dict, runtime_deps=None) -> str:
        return "## Version history\n(reading current checkout only)"

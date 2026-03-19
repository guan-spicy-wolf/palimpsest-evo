"""Recent events context provider (evolvable). Requires runtime_deps["gateway"]."""
from __future__ import annotations
from palimpsest.runtime.interfaces import ContextProvider

class RecentEventsProvider(ContextProvider):
    @property
    def section_type(self) -> str:
        return "recent_events"

    def render(self, job_id: str, workspace: str, section_config: dict, runtime_deps=None) -> str:
        gateway = (runtime_deps or {}).get("gateway")
        if not gateway:
            return "## Recent events\n(event gateway not available)"
        limit = section_config.get("limit", 10)
        fmt = section_config.get("format", "- [{ts}] {type}")
        recent = gateway.recent_events(limit, job_id=job_id)
        lines = []
        for e in recent:
            try:
                lines.append(fmt.format_map({
                    "ts": e.get("ts", "N/A"),
                    "type": e.get("type", "unknown"),
                    "summary": e.get("data", {}).get("summary", ""),
                }))
            except KeyError:
                lines.append(f"- [{e.get('ts', 'N/A')}] {e.get('type', 'unknown')}")
        summary = "\n".join(lines) if lines else "(no recent events)"
        return f"## Recent events\n{summary}"

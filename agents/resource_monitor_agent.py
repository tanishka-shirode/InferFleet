
from services.resource_monitor import get_resource_snapshot


class ResourceMonitorAgent:
    def __init__(self):
        self.name = "Resource Monitor Agent"

    def inspect(self) -> dict:
        snapshot = get_resource_snapshot()
        return {
            "agent": self.name,
            "resources": snapshot,
        }

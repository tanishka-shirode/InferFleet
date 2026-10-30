
from typing import Any


class DecisionAgent:
    """
    Makes resource-aware decisions before local LLM inference.

    EXECUTE: Resource thresholds are satisfied.
    DELAY: Resources are temporarily insufficient.
    REJECT: Server/model is unavailable or RAM is critically low.
    """

    def __init__(
        self,
        min_available_ram_mb: float = 1200,
        max_cpu_percent: float = 90,
        hard_min_ram_mb: float = 500,
    ):
        self.min_available_ram_mb = min_available_ram_mb
        self.max_cpu_percent = max_cpu_percent
        self.hard_min_ram_mb = hard_min_ram_mb

    def decide(
        self,
        resource_snapshot: dict[str, Any],
        lifecycle_status: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate system resources and model readiness."""

        # Support both the current and legacy RAM key names.
        available_ram = float(
            resource_snapshot.get(
                "ram_available_mb",
                resource_snapshot.get("available_ram_mb", 0),
            )
        )

        cpu_percent = float(
            resource_snapshot.get("cpu_percent", 0)
        )

        server_reachable = lifecycle_status.get(
            "server_reachable", False
        )
        model_loaded = lifecycle_status.get(
            "model_loaded", False
        )

        def result(decision: str, reason: str) -> dict[str, Any]:
            return {
                "decision": decision,
                "reason": reason,
                "available_ram_mb": available_ram,
                "cpu_percent": cpu_percent,
            }

        # Check whether the inference server is accessible.
        if not server_reachable:
            return result(
                "REJECT",
                "The local inference server is unreachable.",
            )

        if not model_loaded:
            return result(
                "REJECT",
                "No model is currently loaded.",
            )

        # Prevent starting inference under critical memory pressure.
        if available_ram < self.hard_min_ram_mb:
            return result(
                "REJECT",
                f"Available RAM is critically low "
                f"({available_ram:.0f} MB).",
            )

        reasons = []

        if available_ram < self.min_available_ram_mb:
            reasons.append(
                f"Available RAM is below "
                f"{self.min_available_ram_mb:.0f} MB."
            )

        if cpu_percent >= self.max_cpu_percent:
            reasons.append(
                f"CPU usage is high ({cpu_percent:.1f}%)."
            )

        if reasons:
            return result(
                "DELAY",
                " ".join(reasons)
                + " Retry when system resources improve.",
            )

        return result(
            "EXECUTE",
            "The model is ready and resource thresholds are satisfied.",
        )


if __name__ == "__main__":
    agent = DecisionAgent()

    test_cases = [
        (
            "Healthy resources",
            {"ram_available_mb": 2000, "cpu_percent": 35},
            {"server_reachable": True, "model_loaded": True},
        ),
        (
            "Low available RAM",
            {"ram_available_mb": 850, "cpu_percent": 35},
            {"server_reachable": True, "model_loaded": True},
        ),
        (
            "Critical RAM",
            {"ram_available_mb": 400, "cpu_percent": 35},
            {"server_reachable": True, "model_loaded": True},
        ),
    ]

    for name, resources, lifecycle in test_cases:
        print(f"\n{name}:")
        print(agent.decide(resources, lifecycle))

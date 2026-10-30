
import requests
import psutil


class ModelLifecycleController:
    def __init__(
        self,
        base_url="http://127.0.0.1:8080",
        min_available_ram_mb=1000,
    ):
        self.base_url = base_url.rstrip("/")
        self.min_available_ram_mb = min_available_ram_mb

    def inspect(self) -> dict:
        """Check server availability, loaded model, and available RAM."""
        available_ram_mb = (
            psutil.virtual_memory().available / (1024 ** 2)
        )

        state = {
            "server_reachable": False,
            "model_loaded": False,
            "model_name": None,
            "available_ram_mb": round(available_ram_mb, 2),
            "can_execute": False,
            "decision": None,
        }

        try:
            health = requests.get(
                f"{self.base_url}/health",
                timeout=3,
            )
            health.raise_for_status()

            models_response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5,
            )
            models_response.raise_for_status()

            models = models_response.json().get("data", [])
            state["server_reachable"] = True
            state["model_loaded"] = bool(models)

            if models:
                state["model_name"] = models[0].get("id")

        except requests.RequestException as exc:
            state["decision"] = (
                f"Server unavailable: {exc.__class__.__name__}"
            )
            return state

        if not state["model_loaded"]:
            state["decision"] = "No model is available."
            return state

        if available_ram_mb < self.min_available_ram_mb:
            state["decision"] = (
                "Insufficient available RAM under the configured policy."
            )
            return state

        state["can_execute"] = True
        state["decision"] = (
            "Reuse the loaded model; resource check passed."
        )
        return state

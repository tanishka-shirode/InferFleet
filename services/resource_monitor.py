
import psutil


def get_resource_snapshot() -> dict:
    """Capture a snapshot of system resources."""

    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.2)

    return {
        "cpu_percent": cpu_percent,
        "ram_total_mb": round(memory.total / (1024 ** 2), 2),
        "ram_used_mb": round(memory.used / (1024 ** 2), 2),
        "ram_available_mb": round(memory.available / (1024 ** 2), 2),
        "ram_percent": memory.percent,
    }

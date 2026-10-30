
import json
from datetime import datetime, timezone
from pathlib import Path

from agents.resource_monitor_agent import ResourceMonitorAgent
from agents.inference_executor_agent import InferenceExecutorAgent
from agents.decision_agent import DecisionAgent
from services.model_lifecycle import ModelLifecycleController


def main():
    resource_agent = ResourceMonitorAgent()
    inference_agent = InferenceExecutorAgent()
    decision_agent = DecisionAgent()
    lifecycle = ModelLifecycleController()

    print("\n=== InferFleet: Multi-Agent Inference Manager ===")

    prompt = input("\nEnter your topic or prompt: ").strip()

    if not prompt:
        print("Please enter a non-empty prompt.")
        return

    print("\n[1/6] Inspecting system resources...")
    before = resource_agent.inspect()
    resources = before["resources"]

    print("Resource snapshot:", resources)

    print("\n[2/6] Checking model lifecycle...")
    lifecycle_state = lifecycle.inspect()
    print("Lifecycle:", lifecycle_state)

    print("\n[3/6] Evaluating inference request...")

    # Map the Resource Monitor's field names to the Decision Agent.
    decision = decision_agent.decide(
        resource_snapshot={
            "available_ram_mb": resources.get(
                "ram_available_mb", 0
            ),
            "cpu_percent": resources.get("cpu_percent", 0),
        },
        lifecycle_status={
            "server_reachable": lifecycle_state.get(
                "server_reachable", False
            ),
            "model_loaded": lifecycle_state.get(
                "model_loaded", False
            ),
        },
    )

    print("\n=== Decision Agent ===")
    print("Decision:", decision["decision"])
    print("Reason:", decision["reason"])

    # Both the lifecycle controller and Decision Agent must approve.
    approved = (
        lifecycle_state.get("can_execute", False)
        and decision["decision"] == "EXECUTE"
    )

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    benchmark_file = data_dir / "benchmark_results.jsonl"

    if not approved:
        print("\nInference was not started.")

        if not lifecycle_state.get("can_execute", False):
            print(
                "Lifecycle policy:",
                lifecycle_state.get("decision"),
            )

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "model": lifecycle_state.get("model_name"),
            "metrics": {},
            "lifecycle": lifecycle_state,
            "decision": decision,
            "resources_before": resources,
            "resources_after": resources,
            "verification": {
                "response_received": False,
                "response_non_empty": False,
            },
        }

        with benchmark_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(report) + "\n")

        print(f"Decision record saved to: {benchmark_file}")
        return

    print("\n[4/6] Running local inference...")

    try:
        result = inference_agent.generate(
            prompt=prompt,
            max_tokens=160,
            temperature=0.2,
        )
    except Exception as exc:
        print(f"\nInference failed: {exc}")
        return

    print("\n[5/6] Inspecting resources after inference...")
    after = resource_agent.inspect()

    print("\n[6/6] Recording benchmark...")

    answer = result.get("answer", "").strip()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "model": result.get("model"),
        "metrics": result.get("metrics", {}),
        "lifecycle": lifecycle_state,
        "decision": decision,
        "resources_before": resources,
        "resources_after": after["resources"],
        "verification": {
            "response_received": bool(answer),
            "response_non_empty": bool(answer),
        },
    }

    with benchmark_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(report) + "\n")

    print("\n=== Model Response ===\n")
    print(answer if answer else "The model returned an empty response.")

    print("\n=== Inference Metrics ===")
    for key, value in result.get("metrics", {}).items():
        print(f"{key}: {value}")

    print("\n=== Model Lifecycle ===")
    print(f"Model: {lifecycle_state.get('model_name')}")
    print(f"Lifecycle decision: {lifecycle_state.get('decision')}")
    print(
        f"Available RAM: "
        f"{lifecycle_state.get('available_ram_mb')} MB"
    )

    print("\n=== Decision Agent ===")
    print(f"Decision: {decision['decision']}")
    print(f"Reason: {decision['reason']}")

    print("\n=== Resource Usage ===")
    print("Before:", resources)
    print("After:", after["resources"])

    print(f"\nBenchmark saved to: {benchmark_file}")


if __name__ == "__main__":
    main()

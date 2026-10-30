
import json
import statistics
from pathlib import Path
from datetime import datetime, timezone


class BenchmarkAnalyzerAgent:
    """Analyze real InferFleet benchmark records."""

    def __init__(
        self,
        benchmark_file="data/benchmark_results.jsonl",
        report_file="data/benchmark_analysis.json",
    ):
        self.benchmark_file = Path(benchmark_file)
        self.report_file = Path(report_file)
        self.name = "Benchmark Analyzer Agent"

    def load_records(self):
        """Load valid JSON benchmark records."""
        if not self.benchmark_file.exists():
            raise FileNotFoundError(
                f"Benchmark file not found: {self.benchmark_file}"
            )

        records = []
        invalid_lines = 0

        with self.benchmark_file.open(
            "r", encoding="utf-8"
        ) as file:
            for line in file:
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                    if isinstance(record, dict):
                        records.append(record)
                    else:
                        invalid_lines += 1
                except json.JSONDecodeError:
                    invalid_lines += 1

        return records, invalid_lines

    @staticmethod
    def average(values):
        """Calculate an average from available numeric values."""
        valid_values = [
            value
            for value in values
            if isinstance(value, (int, float))
            and not isinstance(value, bool)
        ]

        if not valid_values:
            return None

        return round(statistics.mean(valid_values), 3)

    def analyze(self):
        """Calculate performance statistics from real benchmark data."""
        records, invalid_lines = self.load_records()

        if not records:
            raise ValueError(
                "No valid benchmark records were found."
            )

        latency = []
        prompt_speed = []
        generation_speed = []
        ram_before = []
        ram_after = []
        token_counts = []

        for record in records:
            metrics = record.get("metrics", {})
            before = record.get("resources_before", {})
            after = record.get("resources_after", {})

            if not isinstance(metrics, dict):
                metrics = {}
            if not isinstance(before, dict):
                before = {}
            if not isinstance(after, dict):
                after = {}

            latency.append(
                metrics.get("client_total_seconds")
            )
            prompt_speed.append(
                metrics.get("prompt_tokens_per_second")
            )
            generation_speed.append(
                metrics.get("generation_tokens_per_second")
            )
            ram_before.append(before.get("ram_available_mb"))
            ram_after.append(after.get("ram_available_mb"))
            token_counts.append(metrics.get("completion_tokens"))

        def valid_numbers(values):
            return [
                value for value in values
                if isinstance(value, (int, float))
                and not isinstance(value, bool)
            ]

        latency_values = valid_numbers(latency)
        speed_values = valid_numbers(generation_speed)

        fastest_run = None
        slowest_run = None

        if latency_values:
            valid_runs = [
                (index, value)
                for index, value in enumerate(latency)
                if isinstance(value, (int, float))
                and not isinstance(value, bool)
            ]

            fastest_index, fastest_time = min(
                valid_runs, key=lambda item: item[1]
            )
            slowest_index, slowest_time = max(
                valid_runs, key=lambda item: item[1]
            )

            fastest_run = {
                "run_number": fastest_index + 1,
                "prompt": records[fastest_index].get("prompt", ""),
                "latency_seconds": fastest_time,
            }
            slowest_run = {
                "run_number": slowest_index + 1,
                "prompt": records[slowest_index].get("prompt", ""),
                "latency_seconds": slowest_time,
            }

        summary = {
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "agent": self.name,
            "total_valid_records": len(records),
            "invalid_lines_skipped": invalid_lines,
            "performance": {
                "average_latency_seconds": self.average(latency),
                "average_prompt_tokens_per_second": self.average(
                    prompt_speed
                ),
                "average_generation_tokens_per_second": self.average(
                    generation_speed
                ),
                "average_completion_tokens": self.average(
                    token_counts
                ),
                "average_available_ram_before_mb": self.average(
                    ram_before
                ),
                "average_available_ram_after_mb": self.average(
                    ram_after
                ),
            },
            "fastest_run": fastest_run,
            "slowest_run": slowest_run,
            "runs": [],
        }

        for index, record in enumerate(records):
            metrics = record.get("metrics", {})
            if not isinstance(metrics, dict):
                metrics = {}

            summary["runs"].append({
                "run_number": index + 1,
                "timestamp": record.get("timestamp"),
                "prompt": record.get("prompt", ""),
                "model": record.get("model"),
                "latency_seconds": metrics.get(
                    "client_total_seconds"
                ),
                "generation_tokens_per_second": metrics.get(
                    "generation_tokens_per_second"
                ),
            })

        self.report_file.parent.mkdir(
            parents=True, exist_ok=True
        )
        with self.report_file.open(
            "w", encoding="utf-8"
        ) as file:
            json.dump(summary, file, indent=4, ensure_ascii=False)

        return summary

    def display_report(self, summary):
        """Display a readable benchmark report."""
        print("\n=== InferFleet Benchmark Analysis ===")
        print(f"Agent: {self.name}")
        print(
            f"Valid benchmark records: "
            f"{summary['total_valid_records']}"
        )
        print(
            f"Invalid lines skipped: "
            f"{summary['invalid_lines_skipped']}"
        )

        print("\n--- Average Performance ---")
        for metric, value in summary["performance"].items():
            label = metric.replace("_", " ").title()
            print(f"{label}: {value if value is not None else 'N/A'}")

        print("\n--- Fastest Run ---")
        print(summary["fastest_run"] or "Latency data unavailable")

        print("\n--- Slowest Run ---")
        print(summary["slowest_run"] or "Latency data unavailable")

        print("\n--- Individual Runs ---")
        for run in summary["runs"]:
            print(
                f"Run {run['run_number']}: "
                f"latency={run['latency_seconds']} seconds, "
                f"generation_speed="
                f"{run['generation_tokens_per_second']} tokens/sec"
            )

        print(f"\nAnalysis saved to: {self.report_file}")


if __name__ == "__main__":
    agent = BenchmarkAnalyzerAgent()

    try:
        report = agent.analyze()
        agent.display_report(report)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Analysis failed: {exc}")

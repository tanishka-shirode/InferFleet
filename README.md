# InferFleet

### Resource-Aware Local LLM Inference Manager

InferFleet is a lightweight, terminal-based project that manages local
Large Language Model (LLM) inference using resource checks and
decision-making agents. It connects to a locally running `llama.cpp`
server, evaluates system readiness before inference, measures
performance, and records benchmark results for later analysis.

The goal is to make local inference more observable and resource-aware,
especially on machines with limited RAM.

------------------------------------------------------------------------

## Key Features

-   **Resource monitoring:** Captures CPU utilization and RAM usage
    using `psutil`.
-   **Model readiness checks:** Checks the local `llama.cpp` server
    health and available model endpoint.
-   **Resource-aware decisions:** Produces `EXECUTE`, `DELAY`, or
    `REJECT` decisions based on configured safeguards and system
    conditions.
-   **Streaming inference:** Sends chat-completion requests to the local
    server and collects streamed response content.
-   **Performance measurements:** Records client-observed time to first
    token (TTFT), total latency, token counts, and token throughput when
    available.
-   **Benchmark logging:** Stores run results in JSON Lines (`.jsonl`)
    format.
-   **Benchmark analysis:** Summarizes previously recorded benchmark
    results.
-   **Terminal-first workflow:** Uses terminal output and log files
    without requiring a web dashboard.

## Architecture

``` mermaid
flowchart TD
    A[Inference Request] --> B[Resource Monitor Agent]
    B --> C[Model Lifecycle Controller]
    C --> D[Decision Agent]
    D -->|EXECUTE| E[Inference Executor Agent]
    D -->|DELAY or REJECT| F[Record Decision]
    E --> G[Measure TTFT and Latency]
    G --> H[Benchmark JSONL Log]
    F --> H
    H --> I[Benchmark Analyzer Agent]
    I --> J[Performance Summary]
```

## Agent Responsibilities

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  Resource Monitor Agent              Collects CPU and memory statistics.

  Model Lifecycle Controller          Checks whether the local inference
                                      server is healthy and a model is
                                      available. It does not load or
                                      unload models.

  Decision Agent                      Evaluates readiness and resource
                                      conditions and chooses whether to
                                      execute, delay, or reject a
                                      request.

  Inference Executor Agent            Streams responses from `llama.cpp`
                                      and records available performance
                                      metrics.

  Benchmark Analyzer Agent            Reads benchmark records and
                                      produces a performance summary.

  Main Pipeline                       Coordinates resource checks,
                                      readiness checks, decisions,
                                      inference, and logging.
  -----------------------------------------------------------------------

## Technology Stack

-   **Python**
-   **uv** --- project and dependency management
-   **llama.cpp** --- local model inference server
-   **Requests** --- HTTP communication with the local server
-   **psutil** --- system resource monitoring
-   **JSON / JSONL** --- run logs and benchmark data

## Benchmarking and Metrics

InferFleet records run results in JSON Lines format and can produce a
benchmark summary. Depending on the server response and record type,
metrics can include:

-   **Time to First Token (TTFT):** Client-observed time from request
    start until the first non-empty response text arrives.
-   **Total latency:** Time from starting the request until the streamed
    response finishes.
-   **Prompt and completion tokens:** Token counts reported by the
    server, when available.
-   **Prompt and generation throughput:** Server-reported rates, when
    available.
-   **Resource snapshots and decisions:** Resource information and the
    pipeline's decision, when recorded.

Some metrics may be unavailable if the server does not return them or if
an older record predates that metric.

### Understanding TTFT

InferFleet measures client-observed TTFT using a monotonic timer. It
includes request and response overhead as well as the time the server
spends processing the prompt before returning the first non-empty text
chunk. It is not necessarily identical to a server-only TTFT
measurement.

## Resource-Aware Decisions

The Decision Agent uses configured policies to decide whether to
proceed. The project includes RAM and CPU safeguards; exact outcomes
depend on the current implementation and configuration.

-   **`EXECUTE`** --- the request passed the configured checks.
-   **`DELAY`** --- the request should wait because current conditions
    are not suitable.
-   **`REJECT`** --- the request was blocked by a configured safety or
    readiness check.

A decision does not guarantee that inference will succeed; the server
can still fail or time out. A rejected request does not necessarily mean
the model itself is broken---it may mean the configured resource policy
is conservative for the available memory.

## Project Structure

The following is a conceptual structure. Actual filenames may vary
slightly with the repository version.

``` text
inferfleet/
├── agents/
│   ├── resource_monitor_agent.py
│   ├── model_lifecycle_controller.py
│   ├── decision_agent.py
│   └── inference_executor_agent.py
├── data/
│   ├── benchmark_results.jsonl
│   └── benchmark_analysis.json
├── main.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## Current Scope and Limitations

-   Uses a locally running `llama.cpp` server; the server must be
    started separately.
-   Checks model/server readiness but does not automatically load or
    unload models.
-   Resource decisions depend on configured thresholds and the current
    machine state.
-   Performance metrics depend on what the local server reports.
-   Uses terminal output and log files; a web dashboard is not required.
-   Does not guarantee that every request will execute when the system
    has limited memory.

## Future Improvements

Potential extensions include a resource-aware request queue, bounded
retry policies, improved memory-capacity estimation, automated model
lifecycle management, and broader benchmark comparisons. These are
future possibilities and are not claimed as implemented features.

## Contributing

Contributions and suggestions are welcome. For a proposed change:

1.  Create a branch for the change.
2.  Keep resource-safety behavior explicit and testable.
3.  Run relevant tests.
4.  Describe the change and its expected impact in the pull request.


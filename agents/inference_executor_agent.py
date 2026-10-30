
import json
import time

import requests


class InferenceExecutorAgent:
    """Runs local LLM inference and measures streaming performance."""

    def __init__(
        self,
        base_url="http://127.0.0.1:8080",
        timeout=300,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def generate(
        self,
        prompt,
        max_tokens=160,
        temperature=0.2,
    ):
        """Generate a response and measure client-observed TTFT."""

        url = f"{self.base_url}/v1/chat/completions"

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant in InferFleet. "
                        "Always respond in clear, natural English by "
                        "default, regardless of the language used in "
                        "the user's message. Do not switch languages "
                        "unless the user explicitly requests another "
                        "language. Keep answers relevant and easy "
                        "to understand."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        request_start = time.perf_counter()
        first_token_time = None
        answer_parts = []
        usage = {}
        server_timings = {}

        with self.session.post(
            url,
            json=payload,
            stream=True,
            timeout=(10, self.timeout),
        ) as response:
            response.raise_for_status()

            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue

                if isinstance(raw_line, bytes):
                    raw_line = raw_line.decode(
                        "utf-8", errors="replace"
                    )

                line = raw_line.strip()

                if not line.startswith("data:"):
                    continue

                data = line[len("data:"):].strip()

                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue

                if isinstance(chunk.get("usage"), dict):
                    usage.update(chunk["usage"])

                if isinstance(chunk.get("timings"), dict):
                    server_timings.update(chunk["timings"])

                for choice in chunk.get("choices", []):
                    delta = choice.get("delta", {})
                    content = delta.get("content", "")

                    if isinstance(content, str) and content:
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                        answer_parts.append(content)

                    elif isinstance(content, list):
                        for item in content:
                            if not isinstance(item, dict):
                                continue

                            text_part = item.get("text", "")

                            if isinstance(text_part, str) and text_part:
                                if first_token_time is None:
                                    first_token_time = time.perf_counter()
                                answer_parts.append(text_part)

        request_end = time.perf_counter()
        answer = "".join(answer_parts).strip()

        total_seconds = request_end - request_start

        ttft_seconds = (
            first_token_time - request_start
            if first_token_time is not None
            else None
        )

        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")

        prompt_ms = server_timings.get("prompt_ms")
        predicted_ms = server_timings.get("predicted_ms")

        prompt_speed = server_timings.get("prompt_per_second")
        generation_speed = server_timings.get("predicted_per_second")

        if prompt_speed is None:
            prompt_speed = server_timings.get(
                "prompt_tokens_per_second"
            )

        if generation_speed is None:
            generation_speed = server_timings.get(
                "predicted_tokens_per_second"
            )

        prompt_seconds = (
            float(prompt_ms) / 1000
            if isinstance(prompt_ms, (int, float))
            else None
        )

        generation_seconds = (
            float(predicted_ms) / 1000
            if isinstance(predicted_ms, (int, float))
            else None
        )

        metrics = {
            "client_total_seconds": round(total_seconds, 6),
            "time_to_first_token_seconds": (
                round(ttft_seconds, 6)
                if ttft_seconds is not None
                else None
            ),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "server_prompt_seconds": prompt_seconds,
            "server_generation_seconds": generation_seconds,
            "prompt_tokens_per_second": prompt_speed,
            "generation_tokens_per_second": generation_speed,
            "cache_tokens_reported": server_timings.get("cache_n"),
        }

        return {
            "agent": "Inference Executor Agent",
            "model": self._get_model_name(),
            "answer": answer,
            "metrics": metrics,
        }

    def _get_model_name(self):
        """Return the loaded model name when available."""
        try:
            response = self.session.get(
                f"{self.base_url}/v1/models",
                timeout=5,
            )
            response.raise_for_status()

            models = response.json().get("data", [])

            if models:
                return models[0].get("id", "local-model")

        except (
            requests.RequestException,
            ValueError,
            TypeError,
        ):
            pass

        return "local-model"


if __name__ == "__main__":
    agent = InferenceExecutorAgent()

    result = agent.generate(
        prompt="Explain LLM inference in simple terms.",
        max_tokens=80,
        temperature=0.2,
    )

    print("\n=== Response ===")
    print(result["answer"])

    print("\n=== Metrics ===")
    print(json.dumps(result["metrics"], indent=2))

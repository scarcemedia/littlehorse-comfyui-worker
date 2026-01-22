from typing import Any

from _pytest.monkeypatch import MonkeyPatch

import pytest


def test_worker_extracts_outputs_inline() -> None:
    from comfyui_worker.worker import _extract_outputs

    history = {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}
    assert _extract_outputs(history) == ["img.png"]


def test_worker_waits_for_history_and_returns_outputs() -> None:
    from comfyui_worker.worker import _execute_workflow

    class StubClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            self.calls.append("submit")
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            self.calls.append("queue")
            return False

        def get_history(self, prompt_id: str) -> dict[str, Any]:
            self.calls.append("history")
            return {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}

    results = _execute_workflow(StubClient(), {"nodes": {}}, "/outputs", lambda *_: None, 2, 600)
    assert results["outputs"] == ["/outputs/img.png"]


def test_worker_times_out_when_queue_never_clears() -> None:
    from comfyui_worker.worker import _execute_workflow

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return True

        def get_history(self, prompt_id: str) -> dict[str, Any]:
            return {}

    with pytest.raises(TimeoutError):
        _execute_workflow(
            StubClient(),
            {"nodes": {}},
            "/outputs",
            lambda *_: None,
            poll_interval=0,
            history_timeout=0,
        )


def test_worker_times_out_when_history_missing() -> None:
    from comfyui_worker.worker import _execute_workflow

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return False

        def get_history(self, prompt_id: str) -> dict[str, Any] | None:
            return None

    with pytest.raises(TimeoutError):
        _execute_workflow(
            StubClient(),
            {"nodes": {}},
            "/outputs",
            lambda *_: None,
            poll_interval=0,
            history_timeout=0,
        )


def test_worker_accepts_empty_history() -> None:
    from comfyui_worker.worker import _execute_workflow

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return False

        def get_history(self, prompt_id: str) -> dict[str, Any]:
            return {}

    results = _execute_workflow(
        StubClient(),
        {"nodes": {}},
        "/outputs",
        lambda *_: None,
        poll_interval=0,
        history_timeout=1,
    )
    assert results["outputs"] == []


def test_worker_preserves_absolute_outputs() -> None:
    from comfyui_worker.worker import _execute_workflow

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return False

        def get_history(self, prompt_id: str) -> dict[str, Any]:
            return {"outputs": {"1": {"images": [{"filename": "/abs/img.png"}]}}}

    results = _execute_workflow(
        StubClient(),
        {"nodes": {}},
        "/outputs",
        lambda *_: None,
        poll_interval=0,
        history_timeout=1,
    )
    assert results["outputs"] == ["/abs/img.png"]


def test_task_entrypoint_logs_progress(monkeypatch: MonkeyPatch) -> None:
    from comfyui_worker.worker import execute_comfyui_workflow

    class StubCtx:
        def __init__(self) -> None:
            self.logs: list[str] = []

        def log(self, message: str) -> None:
            self.logs.append(message)

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return False

        def get_history(self, prompt_id: str) -> dict[str, Any]:
            return {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}

    monkeypatch.setenv("COMFYUI_BASE_URL", "http://localhost:8188")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")

    monkeypatch.setattr(
        "comfyui_worker.worker.ComfyUiClient",
        lambda base_url, timeout, retries: StubClient(),
    )

    ctx = StubCtx()
    result = execute_comfyui_workflow({"nodes": {}}, ctx)

    assert result["prompt_id"] == "pid"
    assert "submit" in ctx.logs[0]

from typing import Any

import pytest


def test_worker_waits_for_history_and_returns_outputs() -> None:
    from comfyui_worker.worker import execute_workflow

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

    results = execute_workflow(StubClient(), {"nodes": {}}, "/outputs", lambda *_: None)
    assert results["outputs"] == ["/outputs/img.png"]


def test_worker_times_out_when_queue_never_clears() -> None:
    from comfyui_worker.worker import execute_workflow

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return True

        def get_history(self, prompt_id: str) -> dict[str, Any]:
            return {}

    with pytest.raises(TimeoutError):
        execute_workflow(
            StubClient(),
            {"nodes": {}},
            "/outputs",
            lambda *_: None,
            poll_interval=0,
            history_timeout=0,
        )


def test_worker_times_out_when_history_missing() -> None:
    from comfyui_worker.worker import execute_workflow

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return False

        def get_history(self, prompt_id: str) -> dict[str, Any] | None:
            return None

    with pytest.raises(TimeoutError):
        execute_workflow(
            StubClient(),
            {"nodes": {}},
            "/outputs",
            lambda *_: None,
            poll_interval=0,
            history_timeout=0,
        )


def test_worker_accepts_empty_history() -> None:
    from comfyui_worker.worker import execute_workflow

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return False

        def get_history(self, prompt_id: str) -> dict[str, Any]:
            return {}

    results = execute_workflow(
        StubClient(),
        {"nodes": {}},
        "/outputs",
        lambda *_: None,
        poll_interval=0,
        history_timeout=1,
    )
    assert results["outputs"] == []


def test_worker_preserves_absolute_outputs() -> None:
    from comfyui_worker.worker import execute_workflow

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return False

        def get_history(self, prompt_id: str) -> dict[str, Any]:
            return {"outputs": {"1": {"images": [{"filename": "/abs/img.png"}]}}}

    results = execute_workflow(
        StubClient(),
        {"nodes": {}},
        "/outputs",
        lambda *_: None,
        poll_interval=0,
        history_timeout=1,
    )
    assert results["outputs"] == ["/abs/img.png"]

from pathlib import Path
import sys
from typing import Any, Awaitable, Callable

import pytest
from _pytest.monkeypatch import MonkeyPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_main_builds_lh_worker(monkeypatch: MonkeyPatch) -> None:
    import main
    from main import build_worker
    from littlehorse.worker import LHTaskWorker

    monkeypatch.setenv("LHW_TASK_NAME", "execute-comfyui-workflow")
    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "1")
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")

    captured: dict[str, Any] = {}

    class StubClient:
        def __init__(self, base_url: str, timeout: float, retries: int) -> None:
            captured["client_args"] = (base_url, timeout, retries)

        def health_check(self) -> bool:
            return True

    async def stub_handler(workflow: dict[str, Any], ctx: Any) -> dict[str, Any]:
        return {"ok": True}

    def stub_build_task_handler(
        client: StubClient,
        output_dir: str,
        poll_interval: int,
        history_timeout: int,
    ) -> Callable[[dict[str, Any], Any], Awaitable[dict[str, Any]]]:
        captured["handler_args"] = (client, output_dir, poll_interval, history_timeout)
        return stub_handler

    monkeypatch.setattr(main, "ComfyUiClient", StubClient)
    monkeypatch.setattr(main, "build_task_handler", stub_build_task_handler)

    worker = build_worker()

    assert isinstance(worker, LHTaskWorker)
    assert worker._task_def_name == "execute-comfyui-workflow"
    assert captured["client_args"] == ("http://comfy", 30.0, 3)


def test_main_builds_worker_with_threads_env(monkeypatch: MonkeyPatch) -> None:
    import main
    from main import build_worker

    monkeypatch.setenv("LHW_TASK_NAME", "execute-comfyui-workflow")
    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "1")
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")

    class StubClient:
        def __init__(self, base_url: str, timeout: float, retries: int) -> None:
            pass

        def health_check(self) -> bool:
            return True

    monkeypatch.setattr(main, "ComfyUiClient", StubClient)

    assert build_worker() is not None


def test_main_requires_threads_env(monkeypatch: MonkeyPatch) -> None:
    from main import build_worker

    monkeypatch.setenv("LHW_TASK_NAME", "execute-comfyui-workflow")
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")
    monkeypatch.delenv("LHW_NUM_WORKER_THREADS", raising=False)
    with pytest.raises(ValueError, match="LHW_NUM_WORKER_THREADS"):
        build_worker()


def test_main_rejects_non_one_threads_env(monkeypatch: MonkeyPatch) -> None:
    from main import build_worker

    monkeypatch.setenv("LHW_TASK_NAME", "execute-comfyui-workflow")
    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "2")
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")
    with pytest.raises(ValueError, match="LHW_NUM_WORKER_THREADS"):
        build_worker()


def test_main_requires_task_name_env(monkeypatch: MonkeyPatch) -> None:
    from main import build_worker

    monkeypatch.delenv("LHW_TASK_NAME", raising=False)
    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "1")
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")
    with pytest.raises(ValueError, match="LHW_TASK_NAME"):
        build_worker()


def test_main_configures_logging_env(monkeypatch: MonkeyPatch) -> None:
    import logging

    from main import configure_logging

    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    configure_logging()
    assert logging.getLogger().level == logging.DEBUG


def test_wait_for_comfyui_returns_on_success() -> None:
    from main import wait_for_comfyui

    class StubClient:
        def health_check(self) -> bool:
            return True

    # Should not raise
    wait_for_comfyui(StubClient(), interval=0, timeout=1)  # type: ignore[arg-type]


def test_wait_for_comfyui_times_out() -> None:
    from main import wait_for_comfyui

    class StubClient:
        def health_check(self) -> bool:
            return False

    with pytest.raises(TimeoutError, match="not available after"):
        wait_for_comfyui(StubClient(), interval=0, timeout=0)  # type: ignore[arg-type]


def test_wait_for_comfyui_retries_until_success() -> None:
    from main import wait_for_comfyui

    class StubClient:
        def __init__(self) -> None:
            self.calls = 0

        def health_check(self) -> bool:
            self.calls += 1
            return self.calls >= 3

    client = StubClient()
    wait_for_comfyui(client, interval=0, timeout=5)  # type: ignore[arg-type]
    assert client.calls == 3

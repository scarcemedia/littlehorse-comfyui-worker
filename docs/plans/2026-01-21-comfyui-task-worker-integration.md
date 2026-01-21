# ComfyUI Task Worker Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the LittleHorse Task Worker entrypoint so the ComfyUI worker registers a task and starts polling for work using the Python SDK.

**Architecture:** Expand configuration for ComfyUI settings, add history retrieval to the ComfyUI client, provide an async task handler wrapper for the existing workflow execution loop, and wire everything into `main.py` with `LHTaskWorker` + `littlehorse.start()`.

**Tech Stack:** Python 3.11+, littlehorse-client, httpx, pydantic, pytest, pytest-anyio.

### Task 1: Expand ComfyUI settings from environment

**Files:**
- Modify: `comfyui_worker/config.py`
- Modify: `tests/test_config.py`

**Step 1: Write the failing test**

```python
def test_settings_from_env_defaults(monkeypatch):
    from comfyui_worker.config import Settings

    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")

    settings = Settings.from_env()
    assert settings.comfyui_base_url == "http://comfy"
    assert settings.comfyui_output_dir == "/outputs"
    assert settings.comfyui_poll_interval_sec == 2
    assert settings.comfyui_history_timeout_sec == 600
    assert settings.comfyui_http_timeout_sec == 30
    assert settings.comfyui_http_retries == 3
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py::test_settings_from_env_defaults -v`
Expected: FAIL because `Settings.from_env` does not exist.

**Step 3: Write minimal implementation**

```python
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    comfyui_base_url: str = Field(..., min_length=1)
    comfyui_output_dir: str = Field(..., min_length=1)
    comfyui_poll_interval_sec: int = Field(2, ge=0)
    comfyui_history_timeout_sec: int = Field(600, ge=0)
    comfyui_http_timeout_sec: int = Field(30, ge=0)
    comfyui_http_retries: int = Field(3, ge=0)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            comfyui_base_url=os.getenv("COMFYUI_BASE_URL"),
            comfyui_output_dir=os.getenv("COMFYUI_OUTPUT_DIR"),
            comfyui_poll_interval_sec=int(os.getenv("COMFYUI_POLL_INTERVAL_SEC", "2")),
            comfyui_history_timeout_sec=int(os.getenv("COMFYUI_HISTORY_TIMEOUT_SEC", "600")),
            comfyui_http_timeout_sec=int(os.getenv("COMFYUI_HTTP_TIMEOUT_SEC", "30")),
            comfyui_http_retries=int(os.getenv("COMFYUI_HTTP_RETRIES", "3")),
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py::test_settings_from_env_defaults -v`
Expected: PASS

**Step 5: Commit**

```bash
git add comfyui_worker/config.py tests/test_config.py
git commit -m "feat: add comfyui settings from env"
```

### Task 2: Add ComfyUI history retrieval

**Files:**
- Modify: `comfyui_worker/comfyui_client.py`
- Modify: `tests/test_comfyui_client.py`

**Step 1: Write the failing test**

```python
def test_get_history_returns_prompt_entry(httpx_mock):
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="GET",
        url="http://comfy/history/pid",
        json={"pid": {"outputs": {}}},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.get_history("pid") == {"outputs": {}}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_comfyui_client.py::test_get_history_returns_prompt_entry -v`
Expected: FAIL because `get_history` does not exist.

**Step 3: Write minimal implementation**

```python
    def get_history(self, prompt_id: str) -> dict[str, Any] | None:
        for attempt in range(self._retries + 1):
            try:
                response = httpx.get(
                    f"{self._base_url}/history/{prompt_id}",
                    timeout=self._timeout,
                )
                response.raise_for_status()
                payload = response.json()
                history = payload.get(prompt_id)
                logger.debug(
                    "Fetched ComfyUI history",
                    extra={"prompt_id": prompt_id, "found": history is not None},
                )
                return history
            except httpx.RequestError:
                if attempt >= self._retries:
                    raise
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status >= 500 and attempt < self._retries:
                    continue
                raise
        return None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_comfyui_client.py::test_get_history_returns_prompt_entry -v`
Expected: PASS

**Step 5: Commit**

```bash
git add comfyui_worker/comfyui_client.py tests/test_comfyui_client.py
git commit -m "feat: add comfyui history retrieval"
```

### Task 3: Async task handler wrapper

**Files:**
- Modify: `comfyui_worker/worker.py`
- Modify: `tests/test_worker.py`

**Step 1: Write the failing test**

```python
import pytest


@pytest.mark.anyio
async def test_task_handler_logs_progress():
    from comfyui_worker.worker import build_task_handler

    class StubCtx:
        def __init__(self):
            self.logs = []

        def log(self, message: str) -> None:
            self.logs.append(message)

    class StubClient:
        def submit_prompt(self, workflow):
            return "pid"

        def is_in_queue(self, prompt_id):
            return False

        def get_history(self, prompt_id):
            return {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}

    handler = build_task_handler(
        client=StubClient(),
        output_dir="/outputs",
        poll_interval=0,
        history_timeout=1,
    )
    ctx = StubCtx()
    result = await handler({"nodes": {}}, ctx)

    assert result["prompt_id"] == "pid"
    assert "submit" in ctx.logs[0]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_worker.py::test_task_handler_logs_progress -v`
Expected: FAIL because `build_task_handler` does not exist.

**Step 3: Write minimal implementation**

```python
import asyncio


def build_task_handler(
    client: Any,
    output_dir: str,
    poll_interval: int,
    history_timeout: int,
):
    async def handler(workflow: dict[str, Any], ctx: WorkerContext) -> dict[str, Any]:
        ctx.log("submit workflow")
        module_logger.info(
            "Executing task",
            extra={"workflow_keys": list(workflow.keys())},
        )
        result = await asyncio.to_thread(
            execute_workflow,
            client,
            workflow,
            output_dir,
            ctx.log,
            poll_interval,
            history_timeout,
        )
        ctx.log("workflow complete")
        module_logger.info(
            "Task complete",
            extra={"prompt_id": result.get("prompt_id")},
        )
        return result

    return handler
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_worker.py::test_task_handler_logs_progress -v`
Expected: PASS

**Step 5: Commit**

```bash
git add comfyui_worker/worker.py tests/test_worker.py
git commit -m "feat: add async task handler"
```

### Task 4: LittleHorse TaskWorker entrypoint

**Files:**
- Modify: `main.py`
- Modify: `tests/test_main.py`

**Step 1: Write the failing test**

```python
def test_main_builds_lh_worker(monkeypatch):
    from littlehorse.worker import LHTaskWorker

    from main import build_worker

    monkeypatch.setenv("LHW_TASK_NAME", "execute-comfyui-workflow")
    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "1")
    monkeypatch.setenv("COMFYUI_BASE_URL", "http://comfy")
    monkeypatch.setenv("COMFYUI_OUTPUT_DIR", "/outputs")

    worker = build_worker()
    assert isinstance(worker, LHTaskWorker)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main.py::test_main_builds_lh_worker -v`
Expected: FAIL because `build_worker` does not return a TaskWorker.

**Step 3: Write minimal implementation**

```python
import asyncio

import littlehorse
from littlehorse.config import LHConfig
from littlehorse.worker import LHTaskWorker

from comfyui_worker.comfyui_client import ComfyUiClient
from comfyui_worker.config import Settings
from comfyui_worker.worker import build_task_handler


def build_worker() -> LHTaskWorker:
    task_name = os.getenv("LHW_TASK_NAME")
    if not task_name:
        raise ValueError("LHW_TASK_NAME must be set")
    threads = os.getenv("LHW_NUM_WORKER_THREADS")
    if not threads:
        raise ValueError("LHW_NUM_WORKER_THREADS must be set to 1")
    if threads != "1":
        raise ValueError("LHW_NUM_WORKER_THREADS must be set to 1")

    settings = Settings.from_env()
    client = ComfyUiClient(
        base_url=settings.comfyui_base_url,
        timeout=settings.comfyui_http_timeout_sec,
        retries=settings.comfyui_http_retries,
    )
    handler = build_task_handler(
        client=client,
        output_dir=settings.comfyui_output_dir,
        poll_interval=settings.comfyui_poll_interval_sec,
        history_timeout=settings.comfyui_history_timeout_sec,
    )
    config = LHConfig()
    worker = LHTaskWorker(handler, task_name, config)
    logger.info("Built task worker", extra={"task_name": task_name})
    return worker


async def main() -> None:
    configure_logging()
    worker = build_worker()
    worker.register_task_def()
    await asyncio.sleep(1.0)
    await littlehorse.start(worker)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_main.py::test_main_builds_lh_worker -v`
Expected: PASS

**Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: wire littlehorse task worker"
```

### Task 5: Regression test pass

**Files:**
- None

**Step 1: Run full test suite**

Run: `uv run pytest`
Expected: PASS

**Step 2: Commit (if needed)**

```bash
git status
```

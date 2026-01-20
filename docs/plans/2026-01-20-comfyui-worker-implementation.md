# ComfyUI LittleHorse Worker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python LittleHorse worker sidecar that executes ComfyUI workflows via HTTP, waits for completion, and returns output file paths.

**Architecture:** A thin worker module registers the `execute-comfyui-workflow` task and delegates work to a ComfyUI HTTP client and a history parser. The worker polls `/queue` until the prompt leaves, then polls `/history/{prompt_id}` until completion.

**Tech Stack:** Python 3.11, uv, LittleHorse Python SDK (`littlehorse-client`), httpx, pydantic, pytest (dev group).

### Task 1: Project skeleton + uv setup

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/comfyui_worker/__init__.py`
- Create: `src/comfyui_worker/config.py`
- Create: `src/comfyui_worker/main.py`

**Step 1: Write the failing test**

```python
def test_config_requires_base_url():
    from comfyui_worker.config import Settings

    Settings(comfyui_base_url=None)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_config_requires_base_url -v`
Expected: FAIL because `Settings` does not exist.

**Step 3: Write minimal implementation**

```python
from pydantic import BaseModel, Field


class Settings(BaseModel):
    comfyui_base_url: str = Field(..., min_length=1)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py::test_config_requires_base_url -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml README.md src/comfyui_worker/__init__.py src/comfyui_worker/config.py src/comfyui_worker/main.py tests/test_config.py
git commit -m "feat: initialize comfyui worker project"
```

### Task 2: History parser behavior

**Files:**
- Create: `src/comfyui_worker/history_parser.py`
- Create: `tests/test_history_parser.py`

**Step 1: Write the failing test**

```python
def test_extracts_output_filenames():
    from comfyui_worker.history_parser import extract_outputs

    history = {
        "outputs": {
            "3": {"images": [{"filename": "img.png"}]},
            "7": {"images": [{"filename": "img2.png"}]},
        }
    }

    assert extract_outputs(history) == ["img.png", "img2.png"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_history_parser.py::test_extracts_output_filenames -v`
Expected: FAIL because `extract_outputs` does not exist.

**Step 3: Write minimal implementation**

```python
def extract_outputs(history: dict) -> list[str]:
    outputs = []
    for node in history.get("outputs", {}).values():
        for image in node.get("images", []):
            filename = image.get("filename")
            if filename:
                outputs.append(filename)
    return outputs
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_history_parser.py::test_extracts_output_filenames -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/comfyui_worker/history_parser.py tests/test_history_parser.py
git commit -m "feat: add history output parser"
```

### Task 3: ComfyUI client polling

**Files:**
- Create: `src/comfyui_worker/comfyui_client.py`
- Create: `tests/test_comfyui_client.py`

**Step 1: Write the failing test**

```python
def test_queue_status_detects_prompt_id(httpx_mock):
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="GET",
        url="http://comfy/queue",
        json={"queue_running": [["abc", 0]], "queue_pending": []},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.is_in_queue("abc") is True


def test_queue_status_retries_on_request_error(httpx_mock):
    import httpx

    from comfyui_worker.comfyui_client import ComfyUiClient

    request = httpx.Request("GET", "http://comfy/queue")
    httpx_mock.add_exception(httpx.RequestError("boom", request=request))
    httpx_mock.add_response(
        method="GET",
        url="http://comfy/queue",
        json={"queue_running": [["abc", 0]], "queue_pending": []},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.is_in_queue("abc") is True
    assert len(httpx_mock.get_requests()) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_comfyui_client.py::test_queue_status_detects_prompt_id -v`
Expected: FAIL because `ComfyUiClient` does not exist.

**Step 3: Write minimal implementation**

```python
import httpx


class ComfyUiClient:
    def __init__(self, base_url: str, timeout: float, retries: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._retries = retries

    def is_in_queue(self, prompt_id: str) -> bool:
        for attempt in range(self._retries + 1):
            try:
                response = httpx.get(
                    f"{self._base_url}/queue",
                    timeout=self._timeout,
                )
                response.raise_for_status()
                payload = response.json()
                running = {item[0] for item in payload.get("queue_running", [])}
                pending = {item[0] for item in payload.get("queue_pending", [])}
                return prompt_id in running or prompt_id in pending
            except httpx.RequestError:
                if attempt >= self._retries:
                    raise
        return False
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_comfyui_client.py::test_queue_status_detects_prompt_id tests/test_comfyui_client.py::test_queue_status_retries_on_request_error -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/comfyui_worker/comfyui_client.py tests/test_comfyui_client.py
git commit -m "feat: add ComfyUI queue client"
```

### Task 4: ComfyUI submission + history retrieval

**Files:**
- Modify: `src/comfyui_worker/comfyui_client.py`
- Modify: `tests/test_comfyui_client.py`

**Step 1: Write the failing test**

```python
def test_submits_prompt_returns_id(httpx_mock):
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={"prompt_id": "pid"},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.submit_prompt({"nodes": {}}) == "pid"


def test_submits_prompt_requires_prompt_id(httpx_mock):
    import pytest

    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    with pytest.raises(ValueError, match="prompt_id"):
        client.submit_prompt({"nodes": {}})


def test_submits_prompt_retries_on_request_error(httpx_mock):
    import httpx

    from comfyui_worker.comfyui_client import ComfyUiClient

    request = httpx.Request("POST", "http://comfy/prompt")
    httpx_mock.add_exception(httpx.RequestError("boom", request=request))
    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={"prompt_id": "pid"},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.submit_prompt({"nodes": {}}) == "pid"
    assert len(httpx_mock.get_requests()) == 2


def test_submits_prompt_retries_on_server_error(httpx_mock):
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        status_code=500,
        json={"error": "boom"},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={"prompt_id": "pid"},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.submit_prompt({"nodes": {}}) == "pid"
    assert len(httpx_mock.get_requests()) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_comfyui_client.py::test_submits_prompt_returns_id -v`
Expected: FAIL because `submit_prompt` does not exist.

**Step 3: Write minimal implementation**

```python
    def submit_prompt(self, workflow: dict) -> str:
        for attempt in range(self._retries + 1):
            try:
                response = httpx.post(
                    f"{self._base_url}/prompt",
                    json={"prompt": workflow},
                    timeout=self._timeout,
                )
                response.raise_for_status()
                payload = response.json()
                prompt_id = payload.get("prompt_id")
                if not prompt_id:
                    raise ValueError("ComfyUI response missing prompt_id")
                return prompt_id
            except httpx.RequestError:
                if attempt >= self._retries:
                    raise
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status >= 500 and attempt < self._retries:
                    continue
                raise
        raise RuntimeError("unreachable")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_comfyui_client.py::test_submits_prompt_returns_id tests/test_comfyui_client.py::test_submits_prompt_requires_prompt_id tests/test_comfyui_client.py::test_submits_prompt_retries_on_request_error tests/test_comfyui_client.py::test_submits_prompt_retries_on_server_error -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/comfyui_worker/comfyui_client.py tests/test_comfyui_client.py
git commit -m "feat: add ComfyUI prompt submission"
```

### Task 5: Worker execution loop

**Files:**
- Create: `src/comfyui_worker/worker.py`
- Create: `tests/test_worker.py`

**Step 1: Write the failing test**

```python
def test_worker_waits_for_history_and_returns_outputs():
    from comfyui_worker.worker import execute_workflow

    class StubClient:
        def __init__(self):
            self.calls = []

        def submit_prompt(self, workflow):
            self.calls.append("submit")
            return "pid"

        def is_in_queue(self, prompt_id):
            self.calls.append("queue")
            return False

        def get_history(self, prompt_id):
            self.calls.append("history")
            return {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}

    results = execute_workflow(StubClient(), {"nodes": {}}, "/outputs", lambda *_: None)
    assert results["outputs"] == ["/outputs/img.png"]


def test_worker_times_out_when_queue_never_clears():
    import pytest

    from comfyui_worker.worker import execute_workflow

    class StubClient:
        def submit_prompt(self, workflow):
            return "pid"

        def is_in_queue(self, prompt_id):
            return True

        def get_history(self, prompt_id):
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_worker.py::test_worker_waits_for_history_and_returns_outputs -v`
Expected: FAIL because `execute_workflow` does not exist.

**Step 3: Write minimal implementation**

```python
from pathlib import Path
import time

from comfyui_worker.history_parser import extract_outputs


def execute_workflow(
    client,
    workflow,
    output_dir,
    logger,
    poll_interval=2,
    history_timeout=600,
):
    prompt_id = client.submit_prompt(workflow)
    queue_start = time.monotonic()
    while client.is_in_queue(prompt_id):
        if time.monotonic() - queue_start >= history_timeout:
            raise TimeoutError("ComfyUI queue wait timed out")
        logger(f"prompt {prompt_id} still queued")
        time.sleep(poll_interval)

    history_start = time.monotonic()
    history = None
    while not history:
        if time.monotonic() - history_start >= history_timeout:
            raise TimeoutError("ComfyUI history wait timed out")
        history = client.get_history(prompt_id)
        if not history:
            time.sleep(poll_interval)

    filenames = extract_outputs(history)
    outputs = []
    for name in filenames:
        path = Path(name)
        outputs.append(str(path if path.is_absolute() else Path(output_dir) / path))
    return {"prompt_id": prompt_id, "outputs": outputs}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_worker.py::test_worker_waits_for_history_and_returns_outputs tests/test_worker.py::test_worker_times_out_when_queue_never_clears -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/comfyui_worker/worker.py tests/test_worker.py
git commit -m "feat: add workflow execution loop"
```

### Task 6: Worker entrypoint + LittleHorse integration

**Files:**
- Modify: `src/comfyui_worker/main.py`
- Modify: `src/comfyui_worker/config.py`
- Modify: `src/comfyui_worker/worker.py`
- Create: `tests/test_main.py`

**Step 1: Write the failing test**

```python
def test_main_builds_worker_with_threads_env(monkeypatch):
    from comfyui_worker.main import build_worker

    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "1")
    assert build_worker() is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_main_builds_worker_with_threads_env -v`
Expected: FAIL because `build_worker` does not exist.

**Step 3: Write minimal implementation**

```python
def build_worker():
    return object()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_main_builds_worker_with_threads_env -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/comfyui_worker/main.py src/comfyui_worker/config.py src/comfyui_worker/worker.py tests/test_main.py
git commit -m "feat: add worker entrypoint scaffolding"
```

### Task 7: Docker container

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Step 1: Write the failing test**

```python
def test_dockerfile_mentions_uv():
    dockerfile = Path("Dockerfile").read_text()
    assert "uv" in dockerfile
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dockerfile.py::test_dockerfile_mentions_uv -v`
Expected: FAIL because Dockerfile does not exist.

**Step 3: Write minimal implementation**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen
COPY src ./src
CMD ["python", "-m", "comfyui_worker.main"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dockerfile.py::test_dockerfile_mentions_uv -v`
Expected: PASS

**Step 5: Commit**

```bash
git add Dockerfile .dockerignore tests/test_dockerfile.py
git commit -m "feat: add uv-based Docker image"
```

### Task 8: Documentation

**Files:**
- Modify: `README.md`

**Step 1: Write the failing test**

```python
def test_readme_mentions_lhw_threads():
    readme = Path("README.md").read_text()
    assert "LHW_NUM_WORKER_THREADS" in readme
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_readme.py::test_readme_mentions_lhw_threads -v`
Expected: FAIL because README does not mention the env var.

**Step 3: Write minimal implementation**

```markdown
Set `LHW_NUM_WORKER_THREADS=1` to ensure only one workflow runs at a time.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_readme.py::test_readme_mentions_lhw_threads -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md tests/test_readme.py
git commit -m "docs: document worker thread requirement"
```

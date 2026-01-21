# ComfyUI Task Signature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a LittleHorse task entrypoint with typed parameters and `WorkerContext` logging aligned to the `generate_image_description` signature style.

**Architecture:** Define a top-level `execute_comfyui_workflow` task function with explicit typing and `ctx: WorkerContext`. Keep core workflow execution in `execute_workflow` and call it from the task, using `ctx.log` for progress updates.

**Tech Stack:** Python 3.11, littlehorse-client, pytest.

### Task 1: Add task entrypoint with WorkerContext

**Files:**
- Modify: `comfyui_worker/worker.py`
- Create: `tests/test_task_entrypoint.py`

**Step 1: Write the failing test**

```python
def test_task_entrypoint_logs_progress():
    from comfyui_worker.worker import execute_comfyui_workflow

    class StubCtx:
        def __init__(self):
            self.logs = []

        def log(self, message):
            self.logs.append(message)

    class StubClient:
        def submit_prompt(self, workflow):
            return "pid"

        def is_in_queue(self, prompt_id):
            return False

        def get_history(self, prompt_id):
            return {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}

    ctx = StubCtx()
    result = execute_comfyui_workflow(
        {"nodes": {}},
        ctx=ctx,
        client=StubClient(),
        output_dir="/outputs",
        poll_interval=0,
        history_timeout=1,
    )

    assert result["prompt_id"] == "pid"
    assert "submit" in ctx.logs[0]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_task_entrypoint.py::test_task_entrypoint_logs_progress -v`
Expected: FAIL because `execute_comfyui_workflow` does not exist.

**Step 3: Write minimal implementation**

```python
from typing import Any

from littlehorse.worker import WorkerContext


def execute_comfyui_workflow(
    workflow: dict[str, Any],
    ctx: WorkerContext,
    client,
    output_dir: str,
    poll_interval: int = 2,
    history_timeout: int = 600,
) -> dict[str, Any]:
    ctx.log("submit workflow")
    result = execute_workflow(
        client,
        workflow,
        output_dir,
        ctx.log,
        poll_interval=poll_interval,
        history_timeout=history_timeout,
    )
    ctx.log("workflow complete")
    return result
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_task_entrypoint.py::test_task_entrypoint_logs_progress -v`
Expected: PASS

**Step 5: Commit**

```bash
```

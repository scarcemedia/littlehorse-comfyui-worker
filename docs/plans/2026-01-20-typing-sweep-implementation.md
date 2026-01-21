# Type Annotation Sweep Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add explicit type annotations to all Python function signatures across production code and tests.

**Architecture:** Keep behavior unchanged while adding `->` return types, parameter annotations, and minimal typing imports. Use `Any` and `Callable` only when concrete types are not available.

**Tech Stack:** Python 3.11, typing, pytest.

### Task 1: Annotate production modules

**Files:**
- Modify: `main.py`
- Modify: `comfyui_worker/comfyui_client.py`
- Modify: `comfyui_worker/config.py`
- Modify: `comfyui_worker/history_parser.py`
- Modify: `comfyui_worker/worker.py`

**Step 1: Write the failing test**

```python
def test_type_hints_present() -> None:
    from comfyui_worker import worker

    assert worker.execute_workflow.__annotations__
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_typing.py::test_type_hints_present -v`
Expected: FAIL because annotations are incomplete.

**Step 3: Write minimal implementation**

```python
def execute_workflow(
    client: Any,
    workflow: dict[str, Any],
    output_dir: str,
    logger: Callable[[str], None],
    poll_interval: int = 2,
    history_timeout: int = 600,
) -> dict[str, Any]:
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_typing.py::test_type_hints_present -v`
Expected: PASS

**Step 5: Commit**

```bash
```

### Task 2: Annotate test modules

**Files:**
- Modify: `tests/*.py`

**Step 1: Write the failing test**

```python
def test_test_functions_are_typed() -> None:
    from tests import test_worker

    assert test_worker.test_worker_accepts_empty_history.__annotations__
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_typing.py::test_test_functions_are_typed -v`
Expected: FAIL because tests lack annotations.

**Step 3: Write minimal implementation**

```python
def test_worker_accepts_empty_history() -> None:
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_typing.py::test_test_functions_are_typed -v`
Expected: PASS

**Step 5: Commit**

```bash
```

# Task Name Config Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Require `LHW_TASK_NAME` to be set at startup so the worker registers a user-defined task name.

**Architecture:** Validate `LHW_TASK_NAME` in `build_worker()` alongside the existing thread validation and update tests/docs accordingly. Keep configuration env-only to match current approach.

**Tech Stack:** Python 3.11, pytest, uv.

### Task 1: Require LHW_TASK_NAME in entrypoint

**Files:**
- Modify: `src/comfyui_worker/main.py`
- Modify: `tests/test_main.py`

**Step 1: Write the failing test**

```python
    from comfyui_worker.main import build_worker

    monkeypatch.delenv("LHW_TASK_NAME", raising=False)
    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "1")
    with pytest.raises(ValueError, match="LHW_TASK_NAME"):
        build_worker()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_main_requires_task_name_env -v`
Expected: FAIL because `build_worker` does not validate `LHW_TASK_NAME`.

**Step 3: Write minimal implementation**

```python
    task_name = os.getenv("LHW_TASK_NAME")
    if not task_name:
        raise ValueError("LHW_TASK_NAME must be set")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_main_requires_task_name_env -v`
Expected: PASS

**Step 5: Commit**

```bash
```

### Task 2: Document required LHW_TASK_NAME

**Files:**
- Modify: `README.md`
- Modify: `tests/test_readme.py`

**Step 1: Write the failing test**

```python
    readme = Path("README.md").read_text()
    assert "LHW_TASK_NAME" in readme
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_readme.py::test_readme_mentions_task_name_env -v`
Expected: FAIL because README lacks the env var.

**Step 3: Write minimal implementation**

```markdown
Set `LHW_TASK_NAME` to the LittleHorse task name this worker should register.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_readme.py::test_readme_mentions_task_name_env -v`
Expected: PASS

**Step 5: Commit**

```bash
```

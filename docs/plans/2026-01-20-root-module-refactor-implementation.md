# Root Module Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move the `comfyui_worker` package to the project root, add a root `main.py` entrypoint, and configure logging with an env override.

**Architecture:** Replace the `src/` layout with a top-level `comfyui_worker/` package and a root `main.py` entrypoint. Update packaging, tests, and Dockerfile to use the new layout, and configure logging via `LOG_LEVEL` with an INFO default.

**Tech Stack:** Python 3.11, pytest, uv, logging.

### Task 1: Update entrypoint and logging

**Files:**
- Create: `main.py`
- Modify: `tests/test_main.py`

**Step 1: Write the failing test**

```python
    import logging

    import main

    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    main.configure_logging()
    assert logging.getLogger().level == logging.DEBUG
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_main_configures_logging_env -v`
Expected: FAIL because `configure_logging` does not exist.

**Step 3: Write minimal implementation**

```python
def configure_logging():
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_main_configures_logging_env -v`
Expected: PASS

**Step 5: Commit**

```bash
```

### Task 2: Move package to root

**Files:**
- Move: `src/comfyui_worker/` -> `comfyui_worker/`
- Modify: `pyproject.toml`
- Modify: `tests/*.py`

**Step 1: Write the failing test**

```python
    import comfyui_worker
    assert hasattr(comfyui_worker, "__file__")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_imports.py::test_imports_use_root_package -v`
Expected: FAIL because package is still under `src/`.

**Step 3: Write minimal implementation**

```python
# Move package directory to the project root.
# Update pyproject packaging config:
# [tool.hatch.build.targets.wheel]
# packages = ["comfyui_worker"]
# Remove pytest pythonpath = ["src"] if present.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_imports.py::test_imports_use_root_package -v`
Expected: PASS

**Step 5: Commit**

```bash
```

### Task 3: Update Dockerfile entrypoint

**Files:**
- Modify: `Dockerfile`
- Modify: `tests/test_dockerfile.py`

**Step 1: Write the failing test**

```python
    dockerfile = Path("Dockerfile").read_text()
    assert "python main.py" in dockerfile
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dockerfile.py::test_dockerfile_runs_root_main -v`
Expected: FAIL because Dockerfile still runs module entrypoint.

**Step 3: Write minimal implementation**

```dockerfile
COPY comfyui_worker ./comfyui_worker
COPY main.py ./
CMD ["python", "main.py"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dockerfile.py::test_dockerfile_runs_root_main -v`
Expected: PASS

**Step 5: Commit**

```bash
```

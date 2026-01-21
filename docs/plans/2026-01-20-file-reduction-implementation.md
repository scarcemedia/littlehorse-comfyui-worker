# File Reduction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce file count by consolidating entrypoints, helpers, and tests while keeping behavior unchanged.

**Architecture:** Remove duplicate entrypoint module, inline history parsing into worker, and merge tests into fewer modules. Update imports and tests accordingly.

**Tech Stack:** Python 3.11, pytest.

### Task 1: Remove duplicate entrypoint module

**Files:**
- Delete: `comfyui_worker/main.py`
- Modify: `main.py`
- Modify: `tests/test_main.py`

**Step 1: Write the failing test**

```python
def test_main_entrypoint_module_exists() -> None:
    import main

    assert hasattr(main, "build_worker")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_main_entrypoint_module_exists -v`
Expected: FAIL after deleting `comfyui_worker/main.py` if imports are wrong.

**Step 3: Write minimal implementation**

```python
# Ensure all entrypoint logic lives only in main.py and tests import main.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_main_entrypoint_module_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
```

### Task 2: Inline history parsing in worker

**Files:**
- Delete: `comfyui_worker/history_parser.py`
- Modify: `comfyui_worker/worker.py`
- Modify: `tests/test_history_parser.py`
- Modify: `tests/test_worker.py`

**Step 1: Write the failing test**

```python
def test_worker_extracts_outputs_inline() -> None:
    from comfyui_worker.worker import _extract_outputs

    history = {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}
    assert _extract_outputs(history) == ["img.png"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_worker.py::test_worker_extracts_outputs_inline -v`
Expected: FAIL because `_extract_outputs` does not exist.

**Step 3: Write minimal implementation**

```python
def _extract_outputs(history: dict[str, Any]) -> list[str]:
    outputs: list[str] = []
    for node in history.get("outputs", {}).values():
        for image in node.get("images", []):
            filename = image.get("filename")
            if filename:
                outputs.append(filename)
    return outputs
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_worker.py::test_worker_extracts_outputs_inline -v`
Expected: PASS

**Step 5: Commit**

```bash
```

### Task 3: Merge tests into fewer modules

**Files:**
- Merge: `tests/test_history_parser.py` into `tests/test_worker.py`
- Merge: `tests/test_task_entrypoint.py` into `tests/test_worker.py`
- Merge: `tests/test_imports.py` into `tests/test_main.py`
- Merge: `tests/test_dockerfile.py` into `tests/test_readme.py` (or a new `tests/test_docs.py`)
- Delete: redundant test files after merge

**Step 1: Write the failing test**

```python
def test_docs_snippet_files() -> None:
    from pathlib import Path

    assert "main.py" in Path("Dockerfile").read_text()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_docs.py::test_docs_snippet_files -v`
Expected: FAIL until merged tests are added.

**Step 3: Write minimal implementation**

```python
# Move test functions into consolidated files and delete redundant modules.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_docs.py::test_docs_snippet_files -v`
Expected: PASS

**Step 5: Commit**

```bash
```

import pytest


def test_main_builds_worker_with_threads_env(monkeypatch):
    from comfyui_worker.main import build_worker

    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "1")
    assert build_worker() is not None


def test_main_requires_threads_env(monkeypatch):
    from comfyui_worker.main import build_worker

    monkeypatch.delenv("LHW_NUM_WORKER_THREADS", raising=False)
    with pytest.raises(ValueError, match="LHW_NUM_WORKER_THREADS"):
        build_worker()


def test_main_rejects_non_one_threads_env(monkeypatch):
    from comfyui_worker.main import build_worker

    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "2")
    with pytest.raises(ValueError, match="LHW_NUM_WORKER_THREADS"):
        build_worker()


def test_main_requires_task_name_env(monkeypatch):
    from comfyui_worker.main import build_worker

    monkeypatch.delenv("LHW_TASK_NAME", raising=False)
    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "1")
    with pytest.raises(ValueError, match="LHW_TASK_NAME"):
        build_worker()

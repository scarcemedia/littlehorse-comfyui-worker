def test_main_builds_worker_with_threads_env(monkeypatch):
    from comfyui_worker.main import build_worker

    monkeypatch.setenv("LHW_NUM_WORKER_THREADS", "1")
    assert build_worker() is not None

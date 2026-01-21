from pathlib import Path


def test_readme_mentions_lhw_threads():
    readme = Path("README.md").read_text()
    assert "LHW_NUM_WORKER_THREADS=1" in readme


def test_readme_mentions_task_name_env():
    readme = Path("README.md").read_text()
    assert "LHW_TASK_NAME" in readme

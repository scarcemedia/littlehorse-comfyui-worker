from pathlib import Path


def test_readme_mentions_lhw_threads():
    readme = Path("README.md").read_text()
    assert "LHW_NUM_WORKER_THREADS" in readme

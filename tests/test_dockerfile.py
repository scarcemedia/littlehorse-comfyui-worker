from pathlib import Path


def test_dockerfile_mentions_uv() -> None:
    dockerfile = Path("Dockerfile").read_text()
    assert "uv" in dockerfile


def test_dockerfile_runs_root_main() -> None:
    dockerfile = Path("Dockerfile").read_text()
    assert "python" in dockerfile
    assert "main.py" in dockerfile

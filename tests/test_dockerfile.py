from pathlib import Path


def test_dockerfile_mentions_uv():
    dockerfile = Path("Dockerfile").read_text()
    assert "uv" in dockerfile

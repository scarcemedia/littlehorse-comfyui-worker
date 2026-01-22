import pytest
from pytest_httpx import HTTPXMock


def test_queue_status_detects_prompt_id(httpx_mock: HTTPXMock) -> None:
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="GET",
        url="http://comfy/queue",
        json={"queue_running": [["abc", 0]], "queue_pending": []},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.is_in_queue("abc") is True


def test_queue_status_retries_on_request_error(httpx_mock: HTTPXMock) -> None:
    import httpx

    from comfyui_worker.comfyui_client import ComfyUiClient

    request = httpx.Request("GET", "http://comfy/queue")
    httpx_mock.add_exception(httpx.RequestError("boom", request=request))
    httpx_mock.add_response(
        method="GET",
        url="http://comfy/queue",
        json={"queue_running": [["abc", 0]], "queue_pending": []},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.is_in_queue("abc") is True
    assert len(httpx_mock.get_requests()) == 2


def test_submits_prompt_returns_id(httpx_mock: HTTPXMock) -> None:
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={"prompt_id": "pid"},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.submit_prompt({"nodes": {}}) == "pid"


def test_submits_prompt_requires_prompt_id(httpx_mock: HTTPXMock) -> None:
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    with pytest.raises(ValueError, match="prompt_id"):
        client.submit_prompt({"nodes": {}})


def test_submits_prompt_retries_on_request_error(httpx_mock: HTTPXMock) -> None:
    import httpx

    from comfyui_worker.comfyui_client import ComfyUiClient

    request = httpx.Request("POST", "http://comfy/prompt")
    httpx_mock.add_exception(httpx.RequestError("boom", request=request))
    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={"prompt_id": "pid"},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.submit_prompt({"nodes": {}}) == "pid"
    assert len(httpx_mock.get_requests()) == 2


def test_submits_prompt_retries_on_server_error(httpx_mock: HTTPXMock) -> None:
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        status_code=500,
        json={"error": "boom"},
    )
    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={"prompt_id": "pid"},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.submit_prompt({"nodes": {}}) == "pid"
    assert len(httpx_mock.get_requests()) == 2


def test_client_get_history_returns_none_when_missing(
    httpx_mock: HTTPXMock,
) -> None:
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(url="http://localhost:8188/history/pid", json={})

    client = ComfyUiClient("http://localhost:8188", timeout=5.0, retries=0)
    result = client.get_history("pid")

    assert result is None


def test_client_get_history_returns_history_when_present(
    httpx_mock: HTTPXMock,
) -> None:
    from comfyui_worker.comfyui_client import ComfyUiClient

    history_data = {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}
    httpx_mock.add_response(
        url="http://localhost:8188/history/pid",
        json={"pid": history_data},
    )

    client = ComfyUiClient("http://localhost:8188", timeout=5.0, retries=0)
    result = client.get_history("pid")

    assert result == history_data


def test_health_check_returns_true_on_success(httpx_mock: HTTPXMock) -> None:
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="GET",
        url="http://comfy/queue",
        json={"queue_running": [], "queue_pending": []},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.health_check() is True


def test_health_check_returns_false_on_connection_error(httpx_mock: HTTPXMock) -> None:
    import httpx

    from comfyui_worker.comfyui_client import ComfyUiClient

    request = httpx.Request("GET", "http://comfy/queue")
    httpx_mock.add_exception(httpx.ConnectError("Connection refused", request=request))

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.health_check() is False


def test_health_check_returns_false_on_http_error(httpx_mock: HTTPXMock) -> None:
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="GET",
        url="http://comfy/queue",
        status_code=500,
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.health_check() is False

import pytest


def test_queue_status_detects_prompt_id(httpx_mock):
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="GET",
        url="http://comfy/queue",
        json={"queue_running": [["abc", 0]], "queue_pending": []},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.is_in_queue("abc") is True


def test_queue_status_retries_on_request_error(httpx_mock):
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


def test_submits_prompt_returns_id(httpx_mock):
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={"prompt_id": "pid"},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.submit_prompt({"nodes": {}}) == "pid"


def test_submits_prompt_requires_prompt_id(httpx_mock):
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="POST",
        url="http://comfy/prompt",
        json={},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    with pytest.raises(ValueError, match="prompt_id"):
        client.submit_prompt({"nodes": {}})


def test_submits_prompt_retries_on_request_error(httpx_mock):
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


def test_submits_prompt_retries_on_server_error(httpx_mock):
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

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

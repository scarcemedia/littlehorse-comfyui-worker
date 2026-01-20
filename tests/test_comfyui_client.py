def test_queue_status_detects_prompt_id(httpx_mock):
    from comfyui_worker.comfyui_client import ComfyUiClient

    httpx_mock.add_response(
        method="GET",
        url="http://comfy/queue",
        json={"queue_running": [["abc", 0]], "queue_pending": []},
    )

    client = ComfyUiClient(base_url="http://comfy", timeout=5, retries=1)
    assert client.is_in_queue("abc") is True

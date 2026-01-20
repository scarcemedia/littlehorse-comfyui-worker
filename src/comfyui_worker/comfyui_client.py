import httpx


class ComfyUiClient:
    def __init__(self, base_url: str, timeout: float, retries: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._retries = retries

    def is_in_queue(self, prompt_id: str) -> bool:
        response = httpx.get(f"{self._base_url}/queue", timeout=self._timeout)
        response.raise_for_status()
        payload = response.json()
        running = {item[0] for item in payload.get("queue_running", [])}
        pending = {item[0] for item in payload.get("queue_pending", [])}
        return prompt_id in running or prompt_id in pending

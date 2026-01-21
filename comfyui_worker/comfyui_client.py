import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ComfyUiClient:
    def __init__(self, base_url: str, timeout: float, retries: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._retries = retries

    def is_in_queue(self, prompt_id: str) -> bool:
        for attempt in range(self._retries + 1):
            try:
                response = httpx.get(
                    f"{self._base_url}/queue",
                    timeout=self._timeout,
                )
                response.raise_for_status()
                payload = response.json()
                running = {item[0] for item in payload.get("queue_running", [])}
                pending = {item[0] for item in payload.get("queue_pending", [])}
                in_queue = prompt_id in running or prompt_id in pending
                logger.debug(
                    "Checked ComfyUI queue",
                    extra={"prompt_id": prompt_id, "in_queue": in_queue},
                )
                return in_queue
            except httpx.RequestError:
                if attempt >= self._retries:
                    raise
        return False

    def submit_prompt(self, workflow: dict[str, Any]) -> str:
        for attempt in range(self._retries + 1):
            try:
                response = httpx.post(
                    f"{self._base_url}/prompt",
                    json={"prompt": workflow},
                    timeout=self._timeout,
                )
                response.raise_for_status()
                payload = response.json()
                prompt_id = payload.get("prompt_id")
                if not prompt_id:
                    raise ValueError("ComfyUI response missing prompt_id")
                logger.info(
                    "Submitted ComfyUI prompt",
                    extra={"prompt_id": prompt_id},
                )
                return prompt_id
            except httpx.RequestError:
                if attempt >= self._retries:
                    raise
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status >= 500 and attempt < self._retries:
                    continue
                raise
        raise RuntimeError("unreachable")

    def get_history(self, prompt_id: str) -> dict[str, Any] | None:
        for attempt in range(self._retries + 1):
            try:
                response = httpx.get(
                    f"{self._base_url}/history/{prompt_id}",
                    timeout=self._timeout,
                )
                response.raise_for_status()
                payload = response.json()
                history = payload.get(prompt_id)
                logger.debug(
                    "Fetched ComfyUI history",
                    extra={"prompt_id": prompt_id, "found": history is not None},
                )
                return history
            except httpx.RequestError:
                if attempt >= self._retries:
                    raise
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status >= 500 and attempt < self._retries:
                    continue
                raise
        return None

import asyncio
import logging
import os
import time

import littlehorse
from littlehorse.config import LHConfig
from littlehorse.worker import LHTaskWorker

from comfyui_worker.comfyui_client import ComfyUiClient
from comfyui_worker.config import load_settings
from comfyui_worker.worker import build_task_handler


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger().setLevel(level)
    logger.info("Logging configured", extra={"level": level_name})


def wait_for_comfyui(
    client: ComfyUiClient,
    interval: int,
    timeout: int,
) -> None:
    """Poll ComfyUI until it responds or timeout is reached."""
    logger.info(
        "Waiting for ComfyUI to become available",
        extra={"interval": interval, "timeout": timeout},
    )
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if client.health_check():
            logger.info("ComfyUI is available")
            return
        logger.debug(
            "ComfyUI not ready, retrying",
            extra={"elapsed": time.monotonic() - start},
        )
        time.sleep(interval)
    raise TimeoutError(f"ComfyUI not available after {timeout}s")


def build_worker() -> LHTaskWorker:
    task_name = os.getenv("LHW_TASK_NAME")
    if not task_name:
        raise ValueError("LHW_TASK_NAME must be set")
    threads = os.getenv("LHW_NUM_WORKER_THREADS")
    if not threads:
        raise ValueError("LHW_NUM_WORKER_THREADS must be set to 1")
    if threads != "1":
        raise ValueError("LHW_NUM_WORKER_THREADS must be set to 1")
    logger.info(
        "Worker configuration validated",
        extra={"task_name": task_name, "threads": threads},
    )

    settings = load_settings()
    client = ComfyUiClient(
        base_url=settings.comfyui_base_url,
        timeout=settings.comfyui_http_timeout_sec,
        retries=settings.comfyui_http_retries,
    )

    # Wait for ComfyUI to be available before registering the task
    wait_for_comfyui(
        client,
        interval=settings.comfyui_health_check_interval_sec,
        timeout=settings.comfyui_health_check_timeout_sec,
    )

    handler = build_task_handler(
        client=client,
        output_dir=settings.comfyui_output_dir,
        poll_interval=settings.comfyui_poll_interval_sec,
        history_timeout=settings.comfyui_history_timeout_sec,
    )
    logger.info(
        "Task handler built",
        extra={
            "task_name": task_name,
            "poll_interval": settings.comfyui_poll_interval_sec,
            "history_timeout": settings.comfyui_history_timeout_sec,
        },
    )

    config = LHConfig()
    worker = LHTaskWorker(handler, task_name, config)
    logger.info("Task worker built", extra={"task_name": task_name})
    return worker


async def main() -> None:
    configure_logging()
    worker = build_worker()
    worker.register_task_def()
    logger.info(
        "Task definition registered",
        extra={"task_name": os.getenv("LHW_TASK_NAME")},
    )
    await asyncio.sleep(1.0)
    await littlehorse.start(worker)


if __name__ == "__main__":
    asyncio.run(main())

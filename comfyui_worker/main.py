import logging
import os


logger = logging.getLogger(__name__)


def build_worker() -> object:
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
    return object()


def main() -> None:
    build_worker()


if __name__ == "__main__":
    main()

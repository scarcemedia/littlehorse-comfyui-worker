import asyncio
from pathlib import Path
import logging
import time
from typing import Any, Awaitable, Callable

from littlehorse.worker import WorkerContext

module_logger = logging.getLogger(__name__)


def _extract_outputs(history: dict[str, Any]) -> list[str]:
    outputs: list[str] = []
    for node in history.get("outputs", {}).values():
        for image in node.get("images", []):
            filename = image.get("filename")
            if filename:
                outputs.append(filename)
    module_logger.debug(
        "Parsed history outputs",
        extra={"output_count": len(outputs)},
    )
    return outputs


def execute_workflow(
    client: Any,
    workflow: dict[str, Any],
    output_dir: str,
    logger: Callable[[str], None],
    poll_interval: int = 2,
    history_timeout: int = 600,
) -> dict[str, Any]:
    prompt_id = client.submit_prompt(workflow)
    module_logger.info("Submitted workflow", extra={"prompt_id": prompt_id})
    queue_start = time.monotonic()
    while client.is_in_queue(prompt_id):
        if time.monotonic() - queue_start >= history_timeout:
            raise TimeoutError("ComfyUI queue wait timed out")
        logger(f"prompt {prompt_id} still queued")
        time.sleep(poll_interval)

    history_start = time.monotonic()
    history = None
    while history is None:
        if time.monotonic() - history_start >= history_timeout:
            raise TimeoutError("ComfyUI history wait timed out")
        history = client.get_history(prompt_id)
        if history is None:
            time.sleep(poll_interval)

    filenames = _extract_outputs(history)
    outputs = []
    for name in filenames:
        path = Path(name)
        outputs.append(str(path if path.is_absolute() else Path(output_dir) / path))
    module_logger.info(
        "Workflow outputs resolved",
        extra={"prompt_id": prompt_id, "output_count": len(outputs)},
    )
    return {"prompt_id": prompt_id, "outputs": outputs}


def execute_comfyui_workflow(
    workflow: dict[str, Any],
    ctx: WorkerContext,
    client: Any,
    output_dir: str,
    poll_interval: int = 2,
    history_timeout: int = 600,
) -> dict[str, Any]:
    ctx.log("submit workflow")
    module_logger.info(
        "Executing task",
        extra={"workflow_keys": list(workflow.keys())},
    )
    result = execute_workflow(
        client,
        workflow,
        output_dir,
        ctx.log,
        poll_interval=poll_interval,
        history_timeout=history_timeout,
    )
    ctx.log("workflow complete")
    module_logger.info(
        "Task complete",
        extra={"prompt_id": result.get("prompt_id")},
    )
    return result


def build_task_handler(
    client: Any,
    output_dir: str,
    poll_interval: int,
    history_timeout: int,
) -> Callable[[dict[str, Any], WorkerContext], Awaitable[dict[str, Any]]]:
    async def handler(workflow: dict[str, Any], ctx: WorkerContext) -> dict[str, Any]:
        ctx.log("submit workflow")
        module_logger.info(
            "Executing task",
            extra={"workflow_keys": list(workflow.keys())},
        )
        result = await asyncio.to_thread(
            execute_workflow,
            client,
            workflow,
            output_dir,
            ctx.log,
            poll_interval,
            history_timeout,
        )
        ctx.log("workflow complete")
        module_logger.info(
            "Task complete",
            extra={"prompt_id": result.get("prompt_id")},
        )
        return result

    return handler

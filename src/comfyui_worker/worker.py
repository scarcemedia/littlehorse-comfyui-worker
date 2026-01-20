from pathlib import Path
import time

from comfyui_worker.history_parser import extract_outputs


def execute_workflow(
    client,
    workflow,
    output_dir,
    logger,
    poll_interval=2,
    history_timeout=600,
):
    prompt_id = client.submit_prompt(workflow)
    queue_start = time.monotonic()
    while client.is_in_queue(prompt_id):
        if time.monotonic() - queue_start >= history_timeout:
            raise TimeoutError("ComfyUI queue wait timed out")
        logger(f"prompt {prompt_id} still queued")
        time.sleep(poll_interval)

    history_start = time.monotonic()
    history = None
    while not history:
        if time.monotonic() - history_start >= history_timeout:
            raise TimeoutError("ComfyUI history wait timed out")
        history = client.get_history(prompt_id)
        if not history:
            time.sleep(poll_interval)

    filenames = extract_outputs(history)
    outputs = []
    for name in filenames:
        path = Path(name)
        outputs.append(str(path if path.is_absolute() else Path(output_dir) / path))
    return {"prompt_id": prompt_id, "outputs": outputs}

from pathlib import Path

from comfyui_worker.history_parser import extract_outputs


def execute_workflow(client, workflow, output_dir, logger):
    prompt_id = client.submit_prompt(workflow)
    while client.is_in_queue(prompt_id):
        logger(f"prompt {prompt_id} still queued")
    history = client.get_history(prompt_id)
    filenames = extract_outputs(history)
    outputs = [str(Path(output_dir) / name) for name in filenames]
    return {"prompt_id": prompt_id, "outputs": outputs}

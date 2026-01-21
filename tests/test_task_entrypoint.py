def test_task_entrypoint_logs_progress():
    from comfyui_worker.worker import execute_comfyui_workflow

    class StubCtx:
        def __init__(self):
            self.logs = []

        def log(self, message):
            self.logs.append(message)

    class StubClient:
        def submit_prompt(self, workflow):
            return "pid"

        def is_in_queue(self, prompt_id):
            return False

        def get_history(self, prompt_id):
            return {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}

    ctx = StubCtx()
    result = execute_comfyui_workflow(
        {"nodes": {}},
        ctx=ctx,
        client=StubClient(),
        output_dir="/outputs",
        poll_interval=0,
        history_timeout=1,
    )

    assert result["prompt_id"] == "pid"
    assert "submit" in ctx.logs[0]

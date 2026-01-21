from typing import Any


def test_task_entrypoint_logs_progress() -> None:
    from comfyui_worker.worker import execute_comfyui_workflow

    class StubCtx:
        def __init__(self) -> None:
            self.logs: list[str] = []

        def log(self, message: str) -> None:
            self.logs.append(message)

    class StubClient:
        def submit_prompt(self, workflow: dict[str, Any]) -> str:
            return "pid"

        def is_in_queue(self, prompt_id: str) -> bool:
            return False

        def get_history(self, prompt_id: str) -> dict[str, Any]:
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

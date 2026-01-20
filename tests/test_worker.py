def test_worker_waits_for_history_and_returns_outputs():
    from comfyui_worker.worker import execute_workflow

    class StubClient:
        def __init__(self):
            self.calls = []

        def submit_prompt(self, workflow):
            self.calls.append("submit")
            return "pid"

        def is_in_queue(self, prompt_id):
            self.calls.append("queue")
            return False

        def get_history(self, prompt_id):
            self.calls.append("history")
            return {"outputs": {"1": {"images": [{"filename": "img.png"}]}}}

    results = execute_workflow(StubClient(), {"nodes": {}}, "/outputs", lambda *_: None)
    assert results["outputs"] == ["/outputs/img.png"]

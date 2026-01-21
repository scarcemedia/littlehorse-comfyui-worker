import logging

from littlehorse import create_workflow_spec
from littlehorse.config import LHConfig
from littlehorse.workflow import Workflow, WorkflowThread


logger = logging.getLogger(__name__)


def _build_workflow(thread: WorkflowThread) -> None:
    workflow_input = thread.declare_json_obj("workflow")
    thread.execute("execute-comfyui-workflow", workflow_input)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = LHConfig()
    workflow = Workflow("comfyui-test-workflow", _build_workflow)
    logger.info("Registering workflow", extra={"workflow": workflow.name})
    create_workflow_spec(workflow, config)


if __name__ == "__main__":
    main()

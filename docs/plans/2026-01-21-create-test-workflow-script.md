# Create Test Workflow Script Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a simple script that registers a LittleHorse workflow calling the `execute-comfyui-workflow` task.

**Architecture:** Create a small Python script at the repo root that builds a minimal workflow with a single task node invoking `execute-comfyui-workflow`, using the LittleHorse Python SDK and env-based config.

**Tech Stack:** Python 3.11+, littlehorse-client.

### Task 1: Add create_test_workflow.py

**Files:**
- Create: `create_test_workflow.py`

**Step 1: Implement the script**

```python
import asyncio
import logging

from littlehorse.config import LHConfig
from littlehorse.workflow import WfSpec


logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = LHConfig()
    wf = WfSpec("comfyui-test-workflow")
    workflow_var = wf.add_variable("workflow")
    wf.add_task("execute-comfyui-workflow", workflow_var)
    logger.info("Registering workflow", extra={"workflow": wf.name})
    await wf.register(config)


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Commit**

```bash
git add create_test_workflow.py
git commit -m "feat: add test workflow registration script"
```

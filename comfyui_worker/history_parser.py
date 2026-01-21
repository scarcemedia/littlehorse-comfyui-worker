import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_outputs(history: dict[str, Any]) -> list[str]:
    outputs: list[str] = []
    for node in history.get("outputs", {}).values():
        for image in node.get("images", []):
            filename = image.get("filename")
            if filename:
                outputs.append(filename)
    logger.debug(
        "Parsed history outputs",
        extra={"output_count": len(outputs)},
    )
    return outputs

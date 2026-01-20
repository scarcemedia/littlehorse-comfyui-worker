def extract_outputs(history: dict) -> list[str]:
    outputs: list[str] = []
    for node in history.get("outputs", {}).values():
        for image in node.get("images", []):
            filename = image.get("filename")
            if filename:
                outputs.append(filename)
    return outputs

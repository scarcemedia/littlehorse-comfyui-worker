def test_extracts_output_filenames() -> None:
    from comfyui_worker.history_parser import extract_outputs

    history = {
        "outputs": {
            "3": {"images": [{"filename": "img.png"}]},
            "7": {"images": [{"filename": "img2.png"}]},
        }
    }

    assert extract_outputs(history) == ["img.png", "img2.png"]

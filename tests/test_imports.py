def test_imports_use_root_package() -> None:
    import comfyui_worker

    assert hasattr(comfyui_worker, "__file__")

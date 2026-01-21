# ComfyUI LittleHorse Worker

This project provides a LittleHorse worker sidecar that executes ComfyUI workflows via HTTP.

## Required configuration

- `LHW_TASK_NAME`: LittleHorse task name this worker should register.
- `LHW_NUM_WORKER_THREADS=1`: Ensures only one workflow runs at a time.
- `LH_HOST`: LittleHorse host or endpoint (for example `localhost:2023`).
- `COMFYUI_BASE_URL`: ComfyUI API base URL (for example `http://127.0.0.1:8188`).
- `COMFYUI_OUTPUT_DIR`: Filesystem path where ComfyUI writes outputs.

## Optional tuning

- `COMFYUI_POLL_INTERVAL_SEC` (default `2`)
- `COMFYUI_HISTORY_TIMEOUT_SEC` (default `600`)
- `COMFYUI_HTTP_TIMEOUT_SEC` (default `30`)
- `COMFYUI_HTTP_RETRIES` (default `3`)
- `LOG_LEVEL` (default `INFO`)

## Running locally

```bash
uv sync --dev
LHW_TASK_NAME=execute-comfyui-workflow \
LHW_NUM_WORKER_THREADS=1 \
LH_HOST=localhost:2023 \
COMFYUI_BASE_URL=http://127.0.0.1:8188 \
COMFYUI_OUTPUT_DIR=/path/to/comfyui/output \
uv run python main.py
```

## Kubernetes sidecar example

Container snippet for a StatefulSet running ComfyUI. The sidecar shares the output volume so it can return file paths.

```yaml
- name: comfyui
  image: comfyui:latest
  ports:
    - containerPort: 8188
  volumeMounts:
    - name: comfyui-output
      mountPath: /comfyui/output

- name: comfyui-worker
  image: worker:latest
  env:
    - name: LHW_TASK_NAME
      value: execute-comfyui-workflow
    - name: LHW_NUM_WORKER_THREADS
      value: "1"
    - name: LH_HOST
      value: littlehorse:2023
    - name: COMFYUI_BASE_URL
      value: http://127.0.0.1:8188
    - name: COMFYUI_OUTPUT_DIR
      value: /comfyui/output
    - name: LOG_LEVEL
      value: INFO
  volumeMounts:
    - name: comfyui-output
      mountPath: /comfyui/output
```

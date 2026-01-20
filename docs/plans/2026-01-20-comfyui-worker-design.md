# ComfyUI LittleHorse Worker Design

## Goals
- Provide a LittleHorse task named `execute-comfyui-workflow` that submits a full ComfyUI workflow JSON, waits for completion, and returns output file paths.
- Run as a Python sidecar (container-first) alongside ComfyUI, using HTTP calls only.
- Log progress while queued/running using LittleHorse task logs.

## Architecture
- Python worker using the LittleHorse Python SDK.
- ComfyUI client module for `/prompt`, `/queue`, and `/history/{prompt_id}` with retry + timeout defaults.
- History parser module to normalize output file paths.

## Configuration
Environment variables:
- `LH_HOST`: LittleHorse host/endpoint.
- `COMFYUI_BASE_URL`: Base URL for the ComfyUI HTTP API.
- `COMFYUI_OUTPUT_DIR`: Output directory for resolving returned filenames.
- `COMFYUI_POLL_INTERVAL_SEC` (default 2).
- `COMFYUI_HISTORY_TIMEOUT_SEC` (default 600).
- `COMFYUI_HTTP_TIMEOUT_SEC` (default 30).
- `COMFYUI_HTTP_RETRIES` (default 3).
- `LHW_NUM_WORKER_THREADS`: Set to `1` to ensure only one job runs at a time.

## Task Input/Output
Input schema:
- `workflow`: full ComfyUI workflow JSON.

Output schema:
- `prompt_id`: ComfyUI prompt id for traceability.
- `outputs`: list of output file paths.

## Execution Flow
1. Receive task and validate `workflow` field.
2. Submit `POST /prompt` with the workflow JSON, capture `prompt_id`.
3. Poll `GET /queue` on an interval.
   - While `prompt_id` appears in `queue_running` or `queue_pending`, log queue status to the task logger.
4. When the prompt id is no longer in the queue, poll `GET /history/{prompt_id}` until a completed history entry is present.
5. Parse outputs from history, resolve against `COMFYUI_OUTPUT_DIR`, return results.

## Error Handling
- Retry network errors/timeouts with exponential backoff.
- Fail fast on non-2xx errors from ComfyUI, logging response bodies.
- If history does not appear before timeout, fail the task with a clear error.
- If history reports failure or contains no outputs, fail with the reported reason.

## Logging
- Log submission, queue polling status, transition to history polling, and completion.
- Keep logs concise to avoid noise while still exposing progress.

## Testing
- Unit tests for ComfyUI client retry/timeout behavior.
- Unit tests for history parsing (multiple nodes, empty outputs, error cases).
- Optional integration test against a local ComfyUI instance.

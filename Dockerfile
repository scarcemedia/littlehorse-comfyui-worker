FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY src ./src

CMD ["python", "-m", "comfyui_worker.main"]

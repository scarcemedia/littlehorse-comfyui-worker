FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv==0.9.18 && uv sync --frozen

COPY src ./src

CMD ["python", "-m", "comfyui_worker.main"]

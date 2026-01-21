FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv==0.9.18 && uv sync --frozen

COPY comfyui_worker ./comfyui_worker
COPY main.py ./

CMD ["uv", "run", "python", "main.py"]

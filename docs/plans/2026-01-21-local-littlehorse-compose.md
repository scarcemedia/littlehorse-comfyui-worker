# Local LittleHorse Compose Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a local docker-compose stack for LittleHorse (server, dashboard) and Kafka, plus a shared development env file for connecting to LittleHorse in dev.

**Architecture:** Create `docker-compose.yml` at the repo root with Kafka, LittleHorse server, and dashboard services matching the provided reference. Add `config/development.env` containing the LittleHorse connection variables for the dashboard and worker.

**Tech Stack:** Docker Compose, LittleHorse server/dashboard images, Kafka (Confluent cp-kafka).

### Task 1: Add docker-compose for Kafka + LittleHorse

**Files:**
- Create: `docker-compose.yml`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_compose_includes_littlehorse_stack() -> None:
    compose = Path("docker-compose.yml").read_text()
    assert "littlehorse" in compose
    assert "littlehorse-dashboard" in compose
    assert "kafka" in compose
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_docker_compose.py::test_compose_includes_littlehorse_stack -v`
Expected: FAIL because `docker-compose.yml` does not exist.

**Step 3: Write minimal implementation**

```yaml
services:
  kafka:
    image: confluentinc/cp-kafka:7.6.1
    container_name: littlehorse_kafka
    environment:
      CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_LOG_DIRS: /tmp/kraft-combined-logs
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: false
    ports:
      - "9092:9092"
    restart: unless-stopped
  littlehorse:
    image: ghcr.io/littlehorse-enterprises/littlehorse/lh-server:0.16.0
    environment:
      LHS_KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      LHS_SHOULD_CREATE_TOPICS: "true"
      LHS_HEALTH_SERVICE_PORT: "1822"
      LHS_CLUSTER_ID: "littlehorse-comfyui-local"
    restart: on-failure
    depends_on:
      kafka:
        condition: service_started
    ports:
      - "2023:2023"
  littlehorse-dashboard:
    image: ghcr.io/littlehorse-enterprises/littlehorse/lh-dashboard:0.16.0
    container_name: littlehorse_dashboard
    environment:
      LHC_API_HOST: littlehorse
      LHC_API_PORT: 2023
      LHC_API_PROTOCOL: PLAIN
      LHC_PORT: 8080
    ports:
      - "53000:3000"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/ || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    restart: unless-stopped
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_docker_compose.py::test_compose_includes_littlehorse_stack -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docker-compose.yml tests/test_docker_compose.py
git commit -m "feat: add local littlehorse compose stack"
```

### Task 2: Add development env file

**Files:**
- Create: `config/development.env`
- Create: `tests/test_dev_env.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_dev_env_contains_littlehorse_vars() -> None:
    env_file = Path("config/development.env").read_text()
    assert "LHC_API_HOST" in env_file
    assert "LHC_API_PORT" in env_file
    assert "LHC_API_PROTOCOL" in env_file
    assert "LHC_PORT" in env_file
    assert "LH_HOST" in env_file
    assert "LHW_TASK_NAME" in env_file
    assert "LHW_NUM_WORKER_THREADS" in env_file
    assert "LOG_LEVEL" in env_file
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dev_env.py::test_dev_env_contains_littlehorse_vars -v`
Expected: FAIL because `config/development.env` does not exist.

**Step 3: Write minimal implementation**

```env
LHC_API_HOST=littlehorse
LHC_API_PORT=2023
LHC_API_PROTOCOL=PLAIN
LHC_PORT=8080
LH_HOST=littlehorse:2023
LHW_TASK_NAME=execute-comfyui-workflow
LHW_NUM_WORKER_THREADS=1
LOG_LEVEL=INFO
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dev_env.py::test_dev_env_contains_littlehorse_vars -v`
Expected: PASS

**Step 5: Commit**

```bash
git add config/development.env tests/test_dev_env.py
git commit -m "feat: add local littlehorse development env"
```

# Data-Collection-Projection
Minimal data collection pipeline that ingests JSON events, normalizes them,
applies privacy/priority rules, and stores rows in SQLite.

## Setup (WSL/Ubuntu)
```bash
conda create -n Data_C python=3.11.14 -y
conda activate Data_C
conda install -y pip
conda install --upgrade pip
pip install -r requirements.txt
```

## Run the core pipeline
```bash
./scripts/init_db.py
./scripts/run_local.sh
```

## Send a test event
```bash
curl -X POST http://127.0.0.1:8080/events \
  -H 'Content-Type: application/json' \
  -d '{"source":"os","app":"EXCEL","event_type":"os.app_focus_block"}'
```

## OS sensors (Windows only)
Sensors send events to the same HTTP ingest endpoint.

```bash
PYTHONPATH=src python -m sensors.os.windows_foreground --ingest-url http://127.0.0.1:8080/events
```

```bash
PYTHONPATH=src python -m sensors.os.windows_idle --ingest-url http://127.0.0.1:8080/events --idle-threshold 900
```

```bash
PYTHONPATH=src python -m sensors.os.file_watcher --ingest-url http://127.0.0.1:8080/events --paths \"~/Documents\"
```

## Config
- `configs/config.yaml` controls DB path, ingest port, validation mode, and queue size.
- `configs/privacy_rules.yaml` controls hashing, masking, and denylist behavior.

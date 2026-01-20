# Data Collector Repository Structure (MVP)

This document lists the **recommended repository/file structure** for the data collection program (up to handing off to the Local Super Agent).

---

## 1) Top-level layout

```text
data-collector/
  README.md
  .gitignore
  requirements.txt
  configs/
    config.yaml                   # allowlist/denylist, retention, sampling, IPC, ports
    privacy_rules.yaml            # masking/hash rules, PII patterns, redaction policies
  schemas/
    event.schema.json             # canonical event envelope schema (validation)
    handoff.schema.json           # handoff package schema (validation)
  migrations/
    001_init.sql                  # SQLite table creation + indexes
  src/
    collector/
      __init__.py
      main.py                     # service entrypoint (wires pipeline)
      config.py                   # config loader + validation
      logging_.py                 # logging setup
      bus.py                      # event ingest (IPC receive) + internal queue
      models.py                   # dataclasses/pydantic models
      normalize.py                # per-source -> canonical envelope normalization
      privacy.py                  # privacy guard: hashing/masking/denylist/allowlist
      priority.py                 # prioritizer + sampler + debounce + blockization
      store.py                    # SQLite persistence (ledger + summaries + queue)
      sessionizer.py              # session boundaries (idle/end events), event merge
      features.py                 # session summaries + feature extraction
      routine.py                  # routine candidate builder (n-gram + periodicity)
      handoff.py                  # generates handoff packages for Local Super Agent
      retention.py                # retention/cleanup jobs
      utils/
        hashing.py                # stable hash helpers + salt mgmt
        masking.py                # title masking, regex-based redaction
        time.py                   # UTC/monotonic helpers, debounce utilities
    sensors/
      os/
        __init__.py
        windows_foreground.py     # active app/window detection (Windows)
        windows_idle.py           # idle detection (Windows)
        file_watcher.py           # file change watcher (watchdog)
        focus_blocker.py          # focus block compression helper (optional)
        emit.py                   # sensor -> core IPC client
      addins/
        __init__.py
        receiver_http.py          # local HTTP receiver for add-in events
        receiver_pipe.py          # named pipe receiver alternative
  tests/
    test_privacy.py
    test_priority.py
    test_sessionizer.py
    test_store.py
  scripts/
    run_local.sh                  # run locally
    init_db.py                    # initializes SQLite database
```

---

## 2) Minimal “first commit” files (must-have)

### Core pipeline (collector/)
- `src/collector/models.py`  
  Canonical types:
  - `EventEnvelope`
  - `FocusBlock`
  - `SessionSummary`
  - `RoutineCandidate`
  - `HandoffPackage`

- `src/collector/store.py` + `migrations/001_init.sql`  
  SQLite schema + persistence (append-only `events` ledger).

- `src/collector/bus.py`  
  Receives incoming events and pushes them into the pipeline (queue).

- `src/collector/normalize.py`  
  Transforms OS/add-in events to the canonical envelope.

- `src/collector/privacy.py`  
  Hashing/masking/denylist enforcement.

- `src/collector/priority.py`  
  P0/P1/P2 routing + debounce + focus block aggregation rules.

- `src/collector/main.py`  
  Wires everything:
  `Ingest -> Normalize -> Privacy -> Priority/Sample -> Store -> Sessionize -> Summarize -> Routine -> Handoff`

### Config + schema
- `configs/config.yaml`
- `configs/privacy_rules.yaml`
- `schemas/event.schema.json`
- `schemas/handoff.schema.json`

---

## 3) OS sensor minimal set (Windows example)

Start with these three sensors + emit client:

- `src/sensors/os/windows_foreground.py`
  - poll every 0.5~1s, **emit only on change**
  - apply debounce (e.g., drop switches shorter than 2s)

- `src/sensors/os/windows_idle.py`
  - emits `idle_start`, `idle_end` to help session boundaries

- `src/sensors/os/file_watcher.py`
  - emits file create/modify/move events (path **not** stored raw; hash in core)

- `src/sensors/os/emit.py`
  - IPC client (local HTTP or named pipe)

---

## 4) Add-in receiver minimal set

Even if you don’t build the add-ins yet, you can implement the **receiver** first:

- `src/sensors/addins/receiver_http.py`
  - `POST /events` on `127.0.0.1:<port>`
  - validates payload, forwards into `collector.bus`

Optional alternative:
- `src/sensors/addins/receiver_pipe.py`
  - named pipe receiver (Windows) / unix socket (mac/linux)

---

## 5) SQLite tables to include in `001_init.sql` (recommended)

Minimum:
- `events` (raw ledger)

Recommended for MVP+:
- `focus_blocks`
- `sessions`
- `routine_candidates`
- `handoff_queue`
- `vault_resources` (optional, encrypted mapping for any plaintext resource)

---

## 6) Build order (implement in this order)

1. `models.py` + `event.schema.json`
2. `001_init.sql` + `store.py`
3. `bus.py` + `main.py` (events can flow into DB)
4. `normalize.py` → `privacy.py` → `priority.py`
5. `sessionizer.py` → `features.py`
6. `routine.py`
7. `handoff.py` + `handoff.schema.json`
8. OS sensors (foreground/idle/file) + `emit.py`
9. add-in receiver (`receiver_http.py`)

---

## 7) Notes

- Keep sensors “dumb”: they emit events; core enforces privacy + storage rules.
- Avoid high-risk collection (keystrokes, screenshots, content). Prefer meta/events.
- Use retention to keep raw events short-lived and store summaries longer.


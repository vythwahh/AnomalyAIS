# AnomalyAIS — Vessel Anomaly Detection Engine

> A deterministic state machine for real-time AIS (Automatic Identification System) signal-loss detection, designed as a foundation for maritime domain awareness and illegal fishing monitoring pipelines.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Domain](https://img.shields.io/badge/Domain-Maritime%20AI-teal) ![Approach](https://img.shields.io/badge/Approach-Rule--Based%20State%20Machine-orange)

---

## The Problem

AIS transponders broadcast vessel position every few seconds. When a vessel goes dark — deliberately or due to equipment failure — the gap in signal is a primary indicator of suspicious behaviour used by organisations like Global Fishing Watch and INTERPOL's Maritime Crime Programme for IUU fishing detection.

The challenge is distinguishing genuine signal loss from noise: transient connectivity drops, satellite coverage gaps, and receiver dead zones all produce false gaps. A naive threshold approach generates too many false positives to be operationally useful.

---

## Design

AnomalyAIS implements a **three-state deterministic FSM** per vessel:

```
         gap > MIN_GAP
OK ─────────────────────► LOST
▲                            │
│   confirmations >= N        │  offline < 10 min → ALERT
│   within CONFIRM_WINDOW     │  offline >= 10 min → CRITICAL
│                            │  every 10 min after → CRITICAL REPEAT
MONITORING ◄─────────────────┘
▲                  │
└──────────────────┘
   monitor_window expires → OK
```

**Key design decisions:**

- **Conservative re-entry** — a vessel is not marked RECOVERED until `CONFIRM_COUNT` pings arrive within `CONFIRM_WINDOW` seconds. This prevents state oscillation from intermittent signal recovery.
- **Tiered alerting** — ALERT fires immediately on loss; CRITICAL fires after 10 minutes; CRITICAL REPEAT fires every 10 minutes thereafter. Downstream systems can triage by severity.
- **Stabilization window** — after recovery, the vessel enters MONITORING state for 1 hour before returning to OK. This flags vessels with unstable AIS behaviour even after they resume broadcasting.
- **Per-vessel isolation** — each `VesselMonitor` instance maintains independent state, making the engine trivially parallelisable across a fleet.

---

## File Structure

```
AnomalyAIS/
├── read_ais.py              # Core VesselMonitor FSM engine
├── generate_ais_bigdata.py  # Synthetic AIS data generator (configurable fleet size)
├── ais_sampler.csv          # Sample AIS input (real-format, anonymised)
└── test_ais_logic.csv       # Unit-test dataset for FSM validation
```

---

## Quick Start

```bash
python read_ais.py
```

Expected output (on `test_ais_logic.csv`):

```
[ALERT] VESSEL_001 lost AIS at 2024-01-01 00:05:00 (gap 0:04:00)
[CRITICAL] VESSEL_001 offline > 10 minutes at 2024-01-01 00:15:00
[INFO] VESSEL_001 regained AIS at 2024-01-01 00:18:00
```

To generate a synthetic large-scale dataset:

```bash
python generate_ais_bigdata.py
```

---

## Configuration

All thresholds are defined at the top of `read_ais.py` and can be tuned per deployment context:

| Parameter | Default | Description |
|---|---|---|
| `MIN_GAP` | 1 second | Minimum gap to trigger LOST state |
| `CRITICAL_10` | 10 minutes | Threshold for first CRITICAL alert |
| `REPEAT_10` | 10 minutes | Interval for CRITICAL REPEAT alerts |
| `CONFIRM_WINDOW` | 3 seconds | Sliding window for recovery confirmation |
| `CONFIRM_COUNT` | 2 pings | Required pings to confirm recovery |
| `MONITOR_WINDOW` | 1 hour | Post-recovery stabilization window |

---

## On the Absence of Real AIS Data

Open AIS datasets with sufficient temporal resolution for anomaly detection are either paywalled (exactEarth, Spire Maritime) or restricted to academic use (NOAA, MarineTraffic). This engine was built against a synthetic dataset generated to match real AIS signal characteristics.

The FSM logic is dataset-agnostic: any CSV with `vessel_id` and `timestamp` columns feeds directly into the engine. In production, this would connect to an AIS stream via NMEA 0183 socket or a message queue (Kafka/Pulsar).

---

## Intended Pipeline Position

```
AIS stream (NMEA / satellite)
        │
        ▼
  Kafka / Pulsar topic
        │
        ▼
   AnomalyAIS FSM          ← this repo
        │
        ▼
  Alert event stream
        │
   ┌────┴────┐
   ▼         ▼
Dashboard  Enforcement
(ops UI)   notification
```

The engine is designed to sit between raw ingestion and downstream alerting — stateless enough to run as a Kafka Streams processor, stateful enough to handle per-vessel context without a separate database.

---

## Background

Built as part of a broader interest in applying data engineering to marine conservation and IUU fishing reduction. The long-term goal is a vessel behaviour monitoring system targeting the East Sea / South China Sea, integrated with species distribution models for tuna habitat prediction.

---

*Author: Nguyễn Triệu Vy Thư · HCMUS Data Science · 2026*

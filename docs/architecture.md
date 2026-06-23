# Architecture

## Overview
LogLens is a modular log analytics platform consisting of a backend written in Python (FastAPI + Polars + DuckDB) and a frontend written in React (Vite + TailwindCSS + TypeScript).

## Components

### Backend
The backend is responsible for receiving log files, parsing them, running high-performance queries using DuckDB, and exposing the analytics data via a REST API.

- **Models**: Defines the unified log schema (`NormalizedLogEntry`) and security schema (`SecurityFinding`) using Pydantic.
- **Parsers**: Abstracted parser classes capable of interpreting specific server logs. Includes an `InferenceParser` for unknown formats.
- **Analytics**: A high-performance analytics engine built over DuckDB to perform aggregates and transformations dynamically.
- **Security Engine**: An extensible detection engine.
  - **Sigma Engine**: Loads Sigma YAML rules and translates them into DuckDB SQL queries.
  - **Custom Detections**: Built-in heuristic detections for common web attacks.
- **Storage**: DuckDB-backed storage for high-performance analytics with support for dataset isolation via `upload_id`.

### Frontend
The frontend presents visual summaries of the analyzed logs.
- Built via React and Vite.
- Dataset isolation is enforced by passing `upload_id` (or `dataset_id`) to all analytics APIs.

## Dataset Isolation Design
All data is stored in a single `log_entries` table in DuckDB. Every entry is associated with an `upload_id`. Analytics queries are strictly scoped using a `WHERE upload_id = ?` clause, ensuring that analytics from different uploads are never mixed.

## Sigma Integration Design
Sigma rules are stored as YAML files in `rules/sigma/`. The `SigmaEngine` parses these rules and converts their `detection` logic into SQL `WHERE` clauses. These clauses are then used to query the `log_entries` table to generate `SecurityFinding` records.

## Future Roadmap
- **Wazuh Connector**: Integrate with Wazuh for advanced host-based security monitoring.
- **Suricata Connector**: Integrate with Suricata for network-based intrusion detection.
- **AI Insights**: Leverage LLMs for automated log analysis and anomaly detection.
- **Real-Time Streaming**: Support for real-time log ingestion and alerting.

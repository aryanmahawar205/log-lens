# LogLens Architecture

# Overview

LogLens is a modular web log analytics and security analysis platform built around two independent processing pipelines:

- Analytics Pipeline
- Security Pipeline

The two pipelines consume the same normalized log records but execute independently.

This separation ensures that failures in one subsystem never impact the other.

---

# High-Level Architecture

```
                    ┌────────────────────┐
                    │    Uploaded Logs   │
                    └─────────┬──────────┘
                              │
                              ▼
                 Automatic Format Detection
                              │
                              ▼
                    Parser Selection Layer
                              │
                              ▼
                   Log Normalization Layer
                              │
                              ▼
                        DuckDB Storage
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       Analytics Pipeline              Security Pipeline
              │                               │
      ┌───────┴────────┐             ┌────────┴────────┐
      ▼                ▼             ▼                 ▼
 GoAccess Engine   DuckDB Fallback Native Detection  Sigma Engine
      │                │             │                 │
      └────────┬───────┘             └────────┬────────┘
               ▼                              ▼
         REST API (FastAPI)           Security Findings
                       │
                       ▼
              React Frontend
```

---

# Upload Pipeline

Every uploaded log follows the same ingestion pipeline.

```
Upload

↓

Format Detection

↓

Parser Selection

↓

Parsing

↓

Normalization

↓

DuckDB Storage

↓

Analytics

↓

Security Detection

↓

Frontend
```

---

# Parser Layer

Supported parsers include:

- Apache Combined
- Apache Common
- Apache Error
- Nginx Access
- Nginx Error
- IIS W3C
- Common Log Format (CLF)

Parser detection is automatic.

The parser registry determines the most suitable parser using confidence scoring.

---

# Normalization

Each parser converts its native log format into a shared schema.

Typical normalized fields include:

- Timestamp
- IP Address
- Method
- URL
- Query String
- Status Code
- Bytes
- User Agent
- Referrer
- Response Time

This canonical schema guarantees every downstream component receives identical data regardless of source format.

---

# Storage Layer

LogLens uses DuckDB as its analytical datastore.

Reasons:

- Embedded database
- Columnar execution
- High-performance aggregations
- Minimal operational overhead
- Excellent OLAP performance

DuckDB powers:

- Log Explorer
- URL Analytics
- Visitor Analytics
- Performance Analytics
- Fallback Analytics

---

# Analytics Pipeline

Analytics are primarily generated using GoAccess.

```
Normalized Logs

↓

Group Compatible Formats

↓

GoAccess Execution

↓

JSON Reports

↓

Merge Results

↓

Dashboard
```

If GoAccess cannot process a dataset, LogLens automatically falls back to DuckDB-based analytics.

Mixed-format uploads are grouped before execution to prevent unsupported formats from affecting valid datasets.

---

# Security Pipeline

Security processing is independent from analytics.

```
Normalized Logs

↓

Security Analyzer

↓

Native Detection
Sigma Engine

↓

Merged Findings

↓

Security Dashboard
```

---

# Native Detection

The native engine performs heuristic detection for common attacks including:

- SQL Injection
- Cross Site Scripting
- Path Traversal
- Directory Enumeration
- Suspicious Requests

Native detection provides fast, lightweight analysis.

---

# Sigma Engine

The Sigma engine provides rule-based security detection.

Features include:

- Recursive rule loading
- Runtime reload
- Rule inventory
- Execution history
- Provider attribution
- Diagnostics
- Official rule library
- Custom rule support

Rules are discovered recursively under:

```
backend/rules/sigma/
```

No filenames are hardcoded.

---

# Validation Framework

LogLens includes a dedicated validation suite.

```
validation/

datasets/

expected_results/

validation_matrix.md

generate_validation.py
```

The validation suite enables deterministic regression testing across:

- Analytics
- Security
- Parsers
- Diagnostics
- UI

---

# Frontend

The frontend is built using:

- React
- TypeScript
- Vite
- Recharts

Major pages include:

- Dashboard
- Traffic
- Performance
- URL Analytics
- Visitor Analytics
- Security
- Log Explorer
- Diagnostics

---

# Design Principles

- Separation of concerns
- Modular architecture
- Provider abstraction
- Format independence
- Offline capable
- Extensible rule ecosystem
- Maintainability
- Open-source friendliness

---

# Future Improvements

Potential future enhancements include:

- Live streaming
- Kafka ingestion
- SIEM export
- OpenTelemetry
- Threat intelligence
- Machine learning anomaly detection
- Multi-user support
- Role-based access control

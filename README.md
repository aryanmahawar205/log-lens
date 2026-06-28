# LogLens

<p align="center">
  <b>A Hybrid Web Log Analytics & Security Analysis Platform</b><br>
  Fast • Extensible • Offline • Developer Friendly
</p>

---

## Overview

LogLens is a modern web log analytics platform that combines **high-performance traffic analytics** with **security detection** in a single application.

Unlike traditional log analyzers that only provide dashboards, LogLens also performs automated security analysis using:

- Native Detection Engine
- Sigma Rule Engine

The platform is designed around a hybrid architecture where each component performs the task it is best suited for.

---

## Key Features

### Analytics

- Apache, Nginx, IIS and CLF log support
- Automatic log format detection
- GoAccess integration
- DuckDB fallback analytics
- Dashboard metrics
- Traffic analytics
- Performance analytics
- URL analytics
- Visitor analytics
- Log explorer
- Mixed-format upload support

### Security

- Native detection engine
- Sigma rule engine
- Dynamic Sigma rule loading
- Recursive rule discovery
- Rule inventory
- Runtime diagnostics
- Security findings explorer
- Provider attribution
- Execution history

### Validation

- Synthetic validation suite
- Attack datasets
- Performance datasets
- Reconnaissance datasets
- Error datasets
- Malformed datasets
- Expected result documentation
- Validation matrix

---

# Architecture

```
                   Upload Log
                        │
                        ▼
             Automatic Format Detection
                        │
                        ▼
                Parser Selection
                        │
                        ▼
            Log Normalization Layer
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 DuckDB Storage                 Security Analyzer
        │                               │
        │                      ┌────────┴────────┐
        │                      ▼                 ▼
        │              Native Detection     Sigma Engine
        │                      │                 │
        └──────────────┬────────┴────────────────┘
                       ▼
              REST API (FastAPI)
                       ▼
              React + TypeScript UI
```

---

# Technology Stack

## Backend

- FastAPI
- Python
- DuckDB
- SQLAlchemy
- Pydantic

## Frontend

- React
- TypeScript
- Vite
- Recharts
- Tailwind CSS

## External Tools

- GoAccess
- Sigma Rules

## Infrastructure

- Docker
- Docker Compose
- GitHub
- Playwright
- Pytest

---

# Upload Pipeline

Whenever a log file is uploaded, LogLens performs the following steps:

1. Detect log format automatically.
2. Select the correct parser.
3. Parse raw log lines.
4. Normalize every record into a common schema.
5. Store normalized logs in DuckDB.
6. Execute analytics pipeline.
7. Execute security pipeline.
8. Return analytics and findings to the frontend.

This normalized schema ensures every analytics and security provider receives identical input regardless of the original log format.

---

# Analytics Pipeline

The analytics subsystem is powered by **GoAccess** with **DuckDB** as a fallback engine.

```
Upload
   │
   ▼
Format Detection
   │
   ▼
GoAccess Grouping
   │
   ▼
GoAccess Execution
   │
   ▼
JSON Report
   │
   ▼
Merged Analytics
   │
   ▼
Dashboard
```

### GoAccess

GoAccess is responsible for:

- request statistics
- visitors
- bandwidth
- traffic trends
- URL analytics
- session analytics

Mixed uploads are grouped by compatible formats before execution, preventing unsupported files from breaking analytics.

If GoAccess cannot process a dataset, LogLens automatically falls back to DuckDB analytics.

---

# Security Pipeline

Security analysis is completely independent from analytics.

```
Normalized Logs
       │
       ▼
Security Analyzer
       │
 ┌─────┴─────────┐
 ▼               ▼
Native      Sigma Engine
Detection
 └─────┬─────────┘
       ▼
Merged Findings
       ▼
Security Dashboard
```

---

# Native Detection

The in-house detection engine performs lightweight heuristic analysis including:

- SQL Injection
- Path Traversal
- XSS
- Directory Enumeration
- Suspicious Requests
- High Risk URLs

Native detection is optimized for speed and immediate execution.

---

# Sigma Engine

LogLens integrates a native Sigma execution engine.

Capabilities include:

- recursive rule discovery
- runtime rule loading
- execution history
- diagnostics
- provider attribution
- rule inventory
- official rule library
- custom rule support

Rule directories:

```
backend/rules/sigma/

official/
custom/
```

New rules can be added without modifying application code.

---

# Validation Suite

A complete validation framework is bundled with the project.

```
validation/

datasets/
normal/
attacks/
performance/
errors/
reconnaissance/
malformed/
mixed/

expected_results/
validation_matrix.md
generate_validation.py
```

The suite validates:

- parser detection
- analytics
- security findings
- Sigma rules
- native detection
- dashboards
- diagnostics

---

# Project Structure

```
backend/
frontend/
docs/
validation/
tests/
data/
docker-compose.yml
README.md
```

---

# Supported Log Formats

- Apache Combined
- Apache Common
- Apache Error
- Nginx Access
- Nginx Error
- IIS W3C
- Common Log Format (CLF)

---

# APIs

Primary API groups include:

- Upload
- Analytics
- Traffic
- Performance
- URLs
- Visitors
- Security
- Diagnostics
- Settings

Interactive API documentation is available via Swagger.

---

# Why DuckDB?

DuckDB was chosen because it provides:

- high-performance analytical queries
- columnar execution
- efficient aggregations
- embedded deployment
- no external database server

It enables fast OLAP-style analysis directly inside LogLens.

---

# Why GoAccess?

GoAccess is a mature, high-performance log analytics engine capable of processing millions of log entries efficiently.

LogLens leverages GoAccess for analytics while extending it with:

- mixed-format processing
- diagnostics
- execution history
- fallback analytics
- unified frontend

---

# Why Sigma?

Sigma provides a vendor-neutral rule format for security detections.

By integrating Sigma, LogLens benefits from a community-maintained ecosystem of web-focused detection rules while allowing custom organizational rules without modifying the application.

---

# Design Principles

- Modular architecture
- Separation of analytics and security
- Format-independent processing
- Extensible rule system
- Offline capable
- Open-source friendly
- Minimal external dependencies
- Maintainable codebase

---

# Running the Project

```bash
git clone <repo>

docker compose up --build
```

Frontend:

```
http://localhost:5173
```

Backend:

```
http://localhost:8000
```

Swagger:

```
http://localhost:8000/docs
```

---

# Future Roadmap

- Live log streaming
- Real-time dashboards
- Alerting
- Role-based access control
- Threat intelligence integration
- SIEM export
- OpenTelemetry support
- Elasticsearch connector
- ML-based anomaly detection

---

# Acknowledgements

This project builds upon several excellent open-source technologies:

- GoAccess
- DuckDB
- Sigma
- FastAPI
- React
- Recharts
- Docker
- Playwright
- Pytest

---

## License

This project is released under the MIT License.

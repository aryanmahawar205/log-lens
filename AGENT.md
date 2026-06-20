# AGENT.md

## Project Name

LogLens

## Mission

Build a modern open-source log analytics platform that significantly improves upon traditional tools such as Webalizer and AWStats.

The platform must ingest web server logs, normalize them into a common schema, perform traffic, performance, and security analytics, and present findings through an interactive web dashboard.

---

## Primary Goal

Convert raw log files into actionable intelligence.

The platform should help users answer:

* Who visited my website?
* What pages were accessed?
* Which endpoints are slow?
* Where are visitors coming from?
* Which errors occur most often?
* Are bots or attackers hitting my site?
* What trends exist over time?

---

## Design Principles

### Extensible

New log parsers should be easily added.

### Scalable

Architecture should support processing millions of log entries.

### Modular

Each component should be independently testable.

### Open

Avoid vendor lock-in.

### Observable

Provide internal metrics and diagnostics.

---

## Core Modules

### ingestion/

Responsible for:

* File discovery
* Upload handling
* Compression handling
* Streaming readers

Supported formats:

* .log
* .gz
* .bz2

---

### parsers/

Implement parsers for:

* Apache Access Logs
* Apache Error Logs
* Nginx Access Logs
* Nginx Error Logs
* IIS W3C Logs
* CLF Logs

All parsers must output a common schema.

---

### normalization/

Transform parsed data into a unified event structure.

Example fields:

* timestamp
* ip
* method
* url
* status_code
* bytes_sent
* response_time
* user_agent
* referrer

---

### analytics/

Traffic analytics.

Metrics:

* Hits
* Visits
* Sessions
* Unique Visitors
* Bandwidth
* URL Rankings

---

### performance/

Performance analytics.

Metrics:

* Average Response Time
* P95
* P99
* Slow Endpoints

---

### security/

Security intelligence.

Detect:

* Brute Force Attempts
* Scanner Activity
* Directory Enumeration
* SQL Injection Probes
* XSS Probes

---

### enrichment/

Provide:

* GeoIP
* ASN Lookup
* Browser Detection
* Device Detection

---

### storage/

Abstract storage layer.

Implement:

* SQLite
* PostgreSQL

---

### api/

FastAPI service exposing analytics.

---

### frontend/

React dashboard.

Requirements:

* Responsive UI
* Dark Mode
* Interactive Charts
* Filtering
* Drill Down Views

---

## Non-Functional Requirements

* Python 3.12+
* Type Hints
* Unit Tests
* Integration Tests
* Docker Support
* CI/CD Ready
* Structured Logging

---

## Success Criteria

The resulting platform should feel closer to Grafana/Kibana than Webalizer while remaining easy to install and use.

Every architectural decision should prioritize usability, performance, extensibility, and clear visual analytics.

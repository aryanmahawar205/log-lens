# LogLens Validation Matrix

This matrix maps each generated dataset to the specific LogLens features and pages it is designed to validate.

| Dataset Category | Datasets Included | Target Parsers | LogLens Feature Validated | LogLens Pages Exercised | Expected Behavior |
| --- | --- | --- | --- | --- | --- |
| **Normal Traffic** | `normal/*` (Small, Medium, Large, Stress) | Apache Combined, Apache Common, Nginx, IIS | Base parsing, auto-detection, GoAccess global analytics, DuckDB sessionization | Dashboard, Traffic, Visitors | Accurate counts of requests, unique visitors, sessions, top URLs, and referrers without triggering security alerts. |
| **Security Attacks** | `attacks/*` (Small, Medium, Large, Stress) | Apache Combined, Nginx | Sigma Rules engine, DuckDB native heuristics (SQLi, XSS, Path Traversal, etc.) | Security, Findings, Diagnostics | Generation of structured security findings, proper provider attribution, and correct severity classifications. |
| **Reconnaissance** | `reconnaissance/*` (Small, Medium, Large, Stress) | Apache Combined | Scanner detection via User-Agent and heuristic brute-force detection | Security, Dashboard | Detections for common scanners (sqlmap, Nikto, Nmap, DirBuster, etc.) using Sigma rules and Native rules. |
| **Performance** | `performance/*` (Small, Medium, Large, Stress) | Nginx | Latency parsing, percentile calculations (P50, P90, P95, P99), bandwidth tracking | Performance, Traffic | Accurate reflection of latency spikes, slow endpoints, and high bandwidth consumption (e.g., large downloads). |
| **Errors** | `errors/*` (Small, Medium, Large, Stress) | Apache Error, Nginx Error | Error log parsing, HTTP status code categorization | Dashboard, Traffic | Proper ingestion of error format logs, and reflection of 4xx and 5xx status codes without crashing the pipeline. |
| **Malformed Logs** | `malformed/*` (Small, Medium, Large, Stress) | Apache Combined (with corrupted lines) | Parser fault tolerance, format fallback detection, error handling | Diagnostics | Parsing should continue gracefully. Malformed lines should be skipped or trigger fallback, and ignored lines should be logged in diagnostics. |
| **Mixed Traffic** | `mixed/*` (Small, Medium, Large, Stress) | Apache Combined | Complete pipeline end-to-end execution, global aggregation, filtering | All Pages | A realistic mix of normal usage, attacks, reconnaissance, errors, and performance anomalies validating overall system stability and accuracy. |

## Feature Coverage Summary

* **Dashboard Page:** Validated by `normal`, `mixed`, `errors`.
* **Traffic Page:** Validated by `normal`, `performance`, `errors`, `mixed`.
* **Visitors Page:** Validated by `normal`, `mixed`.
* **Performance Page:** Validated by `performance`, `mixed`.
* **Security & Findings Page:** Validated by `attacks`, `reconnaissance`, `mixed`.
* **Diagnostics Page:** Validated by `malformed`, `attacks`, `reconnaissance`, `mixed`.

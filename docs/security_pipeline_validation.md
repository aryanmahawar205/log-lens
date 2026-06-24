# Security Pipeline Validation

This document describes the flow of security detection, findings storage, and rendering in LogLens.

## Detection Flow

1. **Upload & Ingestion**: Logs are uploaded via `POST /api/v1/analytics/upload`.
2. **Parsing**: The `CLFParser` or `NginxAccessParser` processes each line.
    - To handle security attacks, parsers use a greedy approach for the URL field and a fallback mechanism for malformed request lines (e.g., where an exploit payload displaces the HTTP protocol).
3. **Security Analysis**: When a security-related API is called, `SecurityAnalyzer` runs several detection methods:
    - **Custom SQLi/XSS/Traversal Detection**: Executes DuckDB SQL queries with `ILIKE` patterns against `url`, `query_string`, and `protocol` fields.
    - **Sigma Engine**: Runs Sigma rules stored in `backend/rules/sigma/` by translating them into DuckDB SQL.
4. **Risk Scoring**: `get_suspicious_ips` aggregates findings per IP and assigns a risk score (0-100) based on severity.

## Findings Flow

- Findings are generated dynamically on request by querying the `log_entries` table.
- Each finding includes:
    - `rule_id`: Identifier for the triggered rule.
    - `severity`: critical, high, medium, or low.
    - `timestamp`: When the attack occurred.
    - `ip`: Attacker's IP address.
    - `evidence`: Specific details (e.g., the URL/Query containing the payload).

## Storage Flow

- Log data is stored in the `log_entries` table in DuckDB.
- Security findings themselves are not persisted separately; they are derived from the raw log data using the detection engines. This ensures that new rules or updated detection logic can be applied retrospectively to existing datasets.

## Rendering Flow

- **Security Analytics Page**: Calls `GET /api/v1/security/findings` and `GET /api/v1/security/overview`.
- **Frontend Components**: Display attack distributions, top suspicious IPs, and a detailed table of security findings with their evidence.

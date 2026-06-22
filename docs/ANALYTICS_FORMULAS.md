# LogLens Analytics Formulas

This document details the internal SQL and logical formulas used by LogLens to compute metrics.

## Traffic Metrics

### Total Requests
Calculates the absolute total number of rows ingested.
`SELECT COUNT(*) FROM log_entries`

### Hits
The total number of successful requests (status 200).
`SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END)`

### Unique Visitors
The total number of distinct IP addresses.
`COUNT(DISTINCT ip)`

### Sessions
Sessions are computed dynamically based on a 30-minute inactivity timeout.
Traffic is partitioned by `(upload_id, ip, user_agent)`. If a request is made more than 1800 seconds (30 minutes) after the previous request in that partition, a new session is started.
We use DuckDB Window Functions (`LAG` and `SUM` over a partition) to dynamically assign a unique string ID to each session block.

### Returning Visitors
A count of distinct IPs that have `session_count > 1`.
`SELECT COUNT(*) FROM user_stats WHERE session_count > 1`

## Performance Metrics

### Latency Percentiles
Percentiles are computed over the `response_time_ms` column, grouped by endpoints.
- **Median (P50)**: `QUANTILE_CONT(response_time_ms, 0.5)`
- **P90**: `QUANTILE_CONT(response_time_ms, 0.90)`
- **P95**: `QUANTILE_CONT(response_time_ms, 0.95)`
- **P99**: `QUANTILE_CONT(response_time_ms, 0.99)`

### Throughput
Bytes transferred per second, calculated by taking the sum of bytes sent in an hour bucket divided by 3600 seconds.
`SUM(bytes_sent) / 3600.0 as bytes_per_second`

## URL Analytics

### Entry Pages
The first URL accessed within a given session window.
`ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY timestamp ASC)` where `rn = 1`.

### Exit Pages
The last URL accessed within a given session window.
`ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY timestamp DESC)` where `rn = 1`.

### Bounce Candidates
Sessions containing exactly 1 page load.
`HAVING COUNT(*) = 1` grouped by `session_id`.

## Security Risk Scoring
A maximum score of 100 is assigned to IPs exhibiting malicious behavior.
- Critical findings (e.g. SQLi, Command Injection): +40 points
- High findings (e.g. XSS, Path Traversal): +25 points
- Medium findings (e.g. Scanners, Enums): +10 points
- Low findings: +5 points

Risk Classifications:
- `Critical`: >= 80 points
- `High`: >= 50 points
- `Medium`: >= 20 points
- `Low`: < 20 points
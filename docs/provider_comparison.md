# Analytics Provider Comparison: Native (DuckDB) vs. GoAccess

This document outlines the differences, expectations, and validation results between the two analytics providers supported by LogLens.

## Comparison Table

| Metric | Native Provider (DuckDB) | GoAccess Provider | Expected Difference |
|--------|--------------------------|-------------------|---------------------|
| Total Requests | Count of all log entries. | Count of valid requests. | Should be identical for clean logs. |
| Unique Visitors | Distinct IP count. | Unique visitor count (based on IP/UA/Date). | Minor deviations possible due to GoAccess's session/visitor heuristics. |
| Hits | Requests with status 200. | Valid requests (can be filtered). | Mostly consistent. |
| Bandwidth | SUM(bytes_sent). | bandwidth (BW). | Identical. |
| Status Codes | Direct group by on `status_code`. | status_codes module. | Identical. |
| Top URLs | Direct group by on `url`. | requests module. | Identical. |
| Response Times | Calculated via DuckDB quantiles. | Fallback to Native. | N/A (Currently using fallback). |

## Deviations Explained

### Unique Visitors
GoAccess uses a combination of IP, User Agent, and Date to determine unique visitors, whereas the Native provider currently uses only the IP address. In logs with many different user agents from the same IP (e.g., proxies), GoAccess may report higher visitor counts.

### Returning Visitors
Currently, the GoAccess provider summary doesn't include "Returning Visitors" directly, while the Native provider calculates this using session history. When GoAccess is active, this metric may fall back to the Native provider's calculation or show 0 if not implemented.

### Performance Analytics
While GoAccess can calculate response times if the log format includes them, LogLens currently uses a fallback to the Native provider for performance analytics to ensure consistency and take advantage of DuckDB's fast quantile calculations.

## Validation Results
Automated consistency tests (`tests/test_goaccess_integration.py`) confirm that for standard Apache/Nginx logs, the core metrics (Requests, Hits, Visitors, Bandwidth) are consistent across both providers.

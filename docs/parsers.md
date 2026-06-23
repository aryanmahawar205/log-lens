# Parser Coverage Report

## Supported Formats
LogLens supports the following log formats out of the box:

- **Apache Access Logs**: Combined and Common formats. Supports optional latency (%D).
- **Apache Error Logs**: Standard error log format.
- **Nginx Access Logs**: Combined format. Supports optional latency ($request_time).
- **Nginx Error Logs**: Standard error log format.
- **IIS W3C Logs**: Standard W3C extended log format.
- **CLF (Common Log Format)**: Standard common log format.
- **JSON Logs**: Line-delimited JSON logs with standard fields (`ip`, `method`, `url`, `status`, `bytes`, `timestamp`, `user_agent`).

## Detection Confidence Approach
When a log file is uploaded, LogLens reads the first 100 lines and runs them through a `FormatDetector`. Each parser implements a `confidence_score(sample_lines)` method:

- **Pattern Matching**: Parsers check if a significant percentage of sample lines match their expected regex.
- **Header Matching**: Some formats (like IIS) are detected by specific header markers (e.g., `#Fields:`).
- **Confidence Rating**: Scores range from 0.0 to 1.0. The parser with the highest score above a threshold (0.5) is selected.

## Schema Inference Workflow
For formats that do not match a known parser, LogLens uses the `InferenceParser`:

1.  **Field Detection**: Uses a series of heuristic regexes to identify:
    -   IP Addresses
    -   HTTP Methods
    -   URLs and Query Strings
    -   Status Codes
    -   Byte counts
    -   Latencies (detecting units like `ms`, `s`, `µs`)
    -   User Agents (detecting browser-like strings)
2.  **Date Parsing**: Loosely searches for bracketed date strings or ISO 8601 timestamps.
3.  **Normalization**: Maps detected fields to the standard `NormalizedLogEntry` schema.

## Fallback Behavior
If detection confidence is very low (e.g., no parser matches > 10% of lines), the system:
- Falls back to `InferenceParser`.
- Labels the format as `UNKNOWN_FORMAT`.
- Attempts to extract as much metadata as possible to provide basic analytics (total requests, top IPs, etc.).

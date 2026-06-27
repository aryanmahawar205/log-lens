# LogLens Validation Suite

The LogLens Validation Suite is a comprehensive set of generated, realistic log datasets designed to serve as the standard regression testing baseline. This suite exercises all application capabilities including log ingestion, auto-detection of formats, parsing, base analytics, performance metrics, and security detections (Sigma and Native heuristics).

## Directory Structure

*   `datasets/`: Contains all generated logs grouped by scenario.
    *   `normal/`: Typical, benign web traffic (home page, API calls, assets).
    *   `attacks/`: Targeted security payloads (SQLi, XSS, LFI/RFI, XXE, SSTI, etc.).
    *   `reconnaissance/`: Traffic from popular security scanners (sqlmap, Nikto, nmap, etc.).
    *   `performance/`: Burst traffic, bandwidth spikes, and high-latency endpoints.
    *   `errors/`: Server error logs and HTTP 4xx/5xx responses.
    *   `malformed/`: Truncated, invalid, or heavily corrupted log entries.
    *   `mixed/`: A production-like combination of all the above.
*   `expected_results/`: Contains `results.json`, documenting the expected parser, line count, and behavioral flags (e.g., `expected_sigma_detections`, `has_malformed`) for every dataset file.
*   `validation_matrix.md`: Maps datasets to the specific LogLens features and UI pages they are designed to validate.
*   `generate_validation.py`: The Python script used to dynamically generate the datasets.

## Dataset Sizes

Each scenario is available in four sizes to support different testing requirements:
*   **Small:** ~50 lines. Ideal for quick unit tests and parser validation.
*   **Medium:** ~500 lines. Ideal for local integration tests and verifying specific Sigma rules.
*   **Large:** ~5,000 lines. Ideal for UI testing and verifying analytics aggregations.
*   **Stress:** ~50,000 lines. Ideal for testing DuckDB performance, out-of-core streaming ingestion, and pipeline bottlenecks.

## Supported Formats

The suite generates logs in the following natively supported formats:
*   **Apache Combined** (`apache_access`)
*   **Apache Common** (`apache_common`)
*   **Apache Error** (`apache_error`)
*   **Nginx Access** (`nginx_access`)
*   **Nginx Error** (`nginx_error`)
*   **IIS W3C** (`iis_w3c`)

## How to use this suite

1.  **Run the Generator (Optional):** If you need to regenerate the logs with different seeds or parameters, run:
    ```bash
    python3 generate_validation.py
    ```
2.  **Run LogLens Validation:**
    *   Upload specific datasets via the LogLens UI or API to trigger ingestion.
    *   Compare the application output (counts, latency, security findings) to the assertions in `expected_results/results.json`.
    *   Use the `validation_matrix.md` to ensure all necessary pages and features have been reviewed.

## Constraints & Architecture Rules

*   **Do not redesign components to fix validation failures.** If a test fails, verify if it's a legitimate bug in the log parser, the analytics engine, or the Sigma rule, and correct the localized component.
*   The system uses **DuckDB** as the primary datastore and **GoAccess** for fast traffic analytics. Security findings rely on **Sigma** rules combined with native SQL detections.

## Expected Behavior Documentation

Refer to `expected_results/results.json` for precise assertions for each file. As a general rule:
*   Logs in `malformed/` should result in non-zero skipped lines in the diagnostics panel.
*   Logs in `attacks/` and `reconnaissance/` must generate Findings in the Security panel.
*   Logs in `performance/` must reflect high percentile latencies (P90, P99) in the Performance panel.

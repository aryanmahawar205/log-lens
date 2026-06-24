# GoAccess Integration Validation

This document provides a procedure to demonstrate and verify the GoAccess integration in LogLens.

## Verification Procedure

### 1. Enable GoAccess
GoAccess is enabled by setting `analytics.provider: goaccess` in `backend/config.yaml`.

### 2. Verify GoAccess Availability
Call the provider API:
`GET /api/v1/system/provider`

Expected Response:
```json
{
  "active_provider": "goaccess",
  "goaccess_available": true,
  ...
}
```

### 3. Trigger GoAccess Execution
Upload a log file and then visit the Dashboard. The dashboard will trigger a call to `GET /api/v1/analytics/overview`.

If the active provider is `goaccess`, `GoAccessAnalyticsProvider` will execute the `goaccess` binary against the raw log file stored in `data/raw_logs/{upload_id}.log`.

### 4. Verify GoAccess Execution Metadata
Check the provider API again or the Integrations status:
`GET /api/v1/system/integrations`

The `goaccess` entry should now contain an `execution` object:
```json
"goaccess": {
  "enabled": true,
  "healthy": true,
  "execution": {
    "last_status": "success",
    "duration": 0.123,
    "metadata": {
      "version": "1.x.x",
      "output_file": "/tmp/...",
      "log_format": "COMBINED"
    }
  }
}
```

### 5. Dashboard Verification
The Dashboard "Provider" field should display **GoAccess** with an orange icon. If a fallback occurred (e.g., binary missing or execution error), it will show **Native** or a **FALLBACK** badge.

## Proof of Execution Procedure

### 1. Execute Analysis
Upload a log file or refresh the dashboard with an active dataset.

### 2. Verify Database Logs
Directly query the DuckDB database to see persisted execution evidence:
`SELECT * FROM external_tool_executions WHERE tool_name = 'goaccess' ORDER BY execution_timestamp DESC LIMIT 1;`

Verify that:
- `status` is 'success'
- `duration_sec` is recorded
- `artifacts` contains paths to JSON and HTML files.

### 3. Verify Filesystem Artifacts
Check the `data/artifacts/goaccess/{upload_id}/` directory.
Ensure both `.json` and `.html` reports exist for the timestamp recorded in the database.

### 4. Consume Diagnostics API
Call `GET /api/v1/system/integrations/goaccess?upload_id={id}`.
Verify the `execution_history` contains the run details and artifact paths.

### 5. Frontend Dashboard Verification
Navigate to the Dashboard and locate the **Diagnostics** panel.
Confirm it shows:
- **Provider**: GoAccess
- **Status**: Success (with emerald shield icon)
- **Processing Time**: Recorded in ms
- **Verification text**: "Data sourced from external binary artifacts"

## Goals Met
- **Visibility**: Users can see exactly which engine produced the analytics.
- **Traceability**: Fallback events are recorded and visible.
- **Evidence**: Version info and processing duration are exposed via the API.
- **Proof of Execution**: Persistent database logs and filesystem artifacts provide undeniable proof of GoAccess usage.

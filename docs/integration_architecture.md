# Integration Architecture

LogLens is designed with a pluggable integration architecture that allows it to leverage both native analytics and external tools.

## Analytics Providers

The core of the analytics system is abstracted behind the `AnalyticsProvider` interface. This allows LogLens to switch between different analytics engines without modifying the frontend or API logic.

### Supported Providers

1.  **NativeAnalyticsProvider (DuckDB):** The default provider. It uses DuckDB and SQL queries to perform analytics directly on normalized log data.
2.  **GoAccessAnalyticsProvider:** An external provider that leverages the GoAccess binary. It works by processing raw log files and ingesting the resulting JSON reports.

### Provider Selection

Provider selection is managed through `backend/config.yaml`:

```yaml
analytics:
  provider: native # or 'goaccess'
```

## Abstraction Layer

The `AnalyticsProvider` base class (`backend/app/analytics/base.py`) defines the contract that all providers must implement. This includes methods for traffic summary, time-series analysis, visitor statistics, and performance metrics.

## Integration Flow (GoAccess Example)

1.  **Log Upload:** When a log file is uploaded, it is saved both to a raw log directory (`data/raw_logs/`) and ingested into the DuckDB database.
2.  **Request:** When an analytics request arrives, the `IntegrationManager` selects the active provider.
3.  **Processing:**
    *   If GoAccess is selected, LogLens executes the `goaccess` binary against the raw log file.
    *   The output is requested in JSON format.
    *   The `GoAccessAnalyticsProvider` maps the GoAccess JSON fields to the LogLens internal models.
4.  **Response:** The unified response is sent back to the frontend.

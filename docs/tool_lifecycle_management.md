# Tool Lifecycle Management

LogLens provides a centralized mechanism for managing the lifecycle, versioning, and health of integrated tools.

## IntegrationManager

The `IntegrationManager` (`backend/app/integration_manager.py`) is responsible for:
*   Tracking registered integrations (GoAccess, Sigma, DuckDB, etc.).
*   Discovering tool versions and health status.
*   Monitoring reload events and timestamps.

## System Integrations API

The health and status of all integrations are exposed via the following endpoint:

`GET /api/v1/system/integrations`

Example Response:

```json
{
  "goaccess": {
    "enabled": true,
    "name": "GoAccess",
    "type": "analytics",
    "version": "1.8.1",
    "healthy": true,
    "last_reload": null
  },
  "sigma": {
    "enabled": true,
    "name": "Sigma",
    "type": "security",
    "version": "1.0.0",
    "healthy": true,
    "rule_count": 124,
    "last_reload": "2023-10-27T10:00:00"
  }
}
```

## Adding New Integrations

To add a new integration:
1.  Register the tool in the `IntegrationManager.__init__` method.
2.  Implement version discovery logic in `get_tool_status`.
3.  If it's an analytics tool, implement the `AnalyticsProvider` interface.

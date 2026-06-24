# Tool Lifecycle Management

LogLens provides a centralized mechanism for managing the lifecycle, versioning, and health of integrated tools.

## IntegrationManager

The `IntegrationManager` (`backend/app/integration_manager.py`) is responsible for:
*   Tracking registered integrations (GoAccess, Sigma, DuckDB, etc.).
*   Discovering tool versions and health status.
*   Monitoring reload events and timestamps.
*   Checking for tool availability before execution.

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

## Maintenance Procedures

### Tool Upgrade Workflow
1.  **Preparation**: Check the tool's release notes for breaking changes in output formats (e.g., GoAccess JSON schema changes).
2.  **Update Binary**: Update the binary on the host system.
3.  **Verification**: Restart the LogLens backend. Use the `GET /api/v1/system/integrations` endpoint to verify the new version is detected and the tool is healthy.
4.  **Regression Testing**: Run the validation framework (`python3 -m pytest tests/test_goaccess_integration.py`) to ensure integration remains functional.

### Version Tracking Workflow
The `IntegrationManager` automatically attempts to discover versions of binary tools by executing them with `--version`. For internal engines (like Sigma or DuckDB), it uses library-specific versioning or hardcoded internal metadata.

## Adding New Integrations

To add a new integration:
1.  Register the tool in the `IntegrationManager.__init__` method or use `register_integration` at runtime.
2.  Implement version discovery and health check logic in `get_tool_status`.
3.  If it's an analytics tool, implement the `AnalyticsProvider` interface and ensure proper fallback logic is in place.

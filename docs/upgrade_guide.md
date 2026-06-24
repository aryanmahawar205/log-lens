# Upgrade Guide

LogLens is designed to be upgrade-safe, ensuring that external tool updates do not require source code modifications.

## Upgrading External Tools

### GoAccess
Since LogLens interacts with GoAccess via the system binary, upgrading GoAccess is as simple as updating the package on the host system:

```bash
sudo apt-get update && sudo apt-get install --only-upgrade goaccess
```

LogLens will automatically detect the new version and display it in the System Integrations dashboard.

### Sigma Rules
Sigma rules are decoupled from the application logic. To update the security detection rules:
1.  Add or remove `.yml` files in `backend/rules/sigma/`.
2.  Trigger a reload (if implemented) or restart the backend.
3.  The `IntegrationManager` will reflect the updated rule count.

## Adding New Providers

New analytics providers can be added by:
1.  Creating a new class inheriting from `AnalyticsProvider`.
2.  Updating `backend/app/api/routes/analytics.py` to recognize the new provider type.
3.  Updating `config.yaml` to use the new provider.

No changes to the frontend or existing dashboard pages are required.

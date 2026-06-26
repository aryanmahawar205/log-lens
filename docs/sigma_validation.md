# Sigma Validation & Integration

## Architecture
LogLens orchestrates external tools to handle various aspects of analytics. For security analytics, it utilizes a pluggable provider architecture, prioritizing Sigma as its primary active engine.

The Sigma engine operates on DuckDB, executing dynamic SQL constructed by compiling standard Sigma rules (`.yml` files).

## Rule Lifecycle

1. **Rule Loading**: Rules are loaded from `rules/sigma/` upon backend startup or when manually triggered.
2. **Rule Validation**: The engine parses rules ensuring `detection` and `condition` keys exist. Valid rules are converted to DuckDB dialects; invalid rules are safely ignored, tracked as errors.
3. **Execution**: Incoming parsed log lines are normalized (e.g., malformed lines decode appropriately so query strings and URLs end up in the correct fields). The Sigma engine dynamically applies logical groupings (AND/OR) using the normalized data model to detect threats.
4. **Reload Procedure**: To reload rules seamlessly, issue a POST request to `/api/v1/security/rules/reload`.

## Adding New Rules
1. Add standard Sigma `.yml` file in `backend/rules/sigma/`.
2. Do not restart the server; trigger the reload endpoint. LogLens will dynamically load it without modifying application source code.

## Troubleshooting
- Diagnostics are exposed at `SystemDiagnostics.tsx` to visualize: execution count, loaded rules, engine provider state, execution duration, and potential exceptions (last error).
- Look into malformed request ingestion inside `backend/app/parsers/` if certain values aren't triggering expected rules.

## Known Limitations
- The condition engine supports basic `AND`, `OR`, `NOT`, and `1 of selection*` operations. Very advanced Sigma condition modifiers or correlation rules aren't completely supported yet.

## Validation Methodology
Tests validate rule ingestion and engine logic (e.g., `test_sigma_validation.py`). It explicitly checks that payloads like `id=1 UNION SELECT` accurately hit `selection_url or selection_query`.

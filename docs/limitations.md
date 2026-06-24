# Known Limitations & TODOs

## Known Limitations
- **Memory Consumption**: Large log files (multi-GB) are currently loaded into a temporary file before processing. For extremely high-volume environments, a fully streaming architecture would be preferred.
- **Schema Evolution**: The `NormalizedLogEntry` schema is relatively rigid. Adding custom fields for niche log formats requires code changes.
- **Sigma Support**: The current Sigma engine is minimalist and supports a subset of Sigma features (e.g., `contains` modifier and basic boolean logic). Complex conditions or aggregations in Sigma rules are not yet supported.
- **Dataset Deletion**: Deleting a dataset removes records from DuckDB but does not immediately shrink the `.duckdb` file size on disk due to how DuckDB manages storage.
- **GoAccess Integration**:
    - Performance analytics (quantiles, response times) are currently calculated using the Native provider fallback.
    - Top User Agents and complex session metrics (e.g., returning visitors) in the GoAccess provider summary may fall back to Native provider or show limited data.
    - Custom GoAccess configuration files are not yet supported via the LogLens provider interface.

## Remaining TODOs
- [ ] Implement support for compressed log files (.gz, .zip).
- [ ] Add support for CSV log formats with customizable headers.
- [ ] Enhance Sigma engine with more modifiers (`startswith`, `endswith`, `re`).
- [ ] Implement user authentication and multi-tenancy.
- [ ] Add real-time log tailing and visualization.
- [ ] Add support for custom GoAccess configuration mapping for unknown log formats.

## Scalability Concerns
- **Single-Node Storage**: DuckDB is an embedded database. While extremely fast for analytics, it is limited to a single node. High-concurrency or distributed needs would require migrating to a backend like MotherDuck or a distributed OLAP database.
- **Frontend Performance**: Rendering tables with thousands of security findings can impact browser performance. Virtualized lists or better pagination are recommended for scale.
- **GoAccess Execution**: For each analytics request, GoAccess is executed on the raw log file. While fast for small-to-medium files, this could become a bottleneck for very large files or frequent concurrent requests.

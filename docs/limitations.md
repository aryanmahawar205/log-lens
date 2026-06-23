# Known Limitations & TODOs

## Known Limitations
- **Memory Consumption**: Large log files (multi-GB) are currently loaded into a temporary file before processing. For extremely high-volume environments, a fully streaming architecture would be preferred.
- **Schema Evolution**: The `NormalizedLogEntry` schema is relatively rigid. Adding custom fields for niche log formats requires code changes.
- **Sigma Support**: The current Sigma engine is minimalist and supports a subset of Sigma features (e.g., `contains` modifier and basic boolean logic). Complex conditions or aggregations in Sigma rules are not yet supported.
- **Dataset Deletion**: Deleting a dataset removes records from DuckDB but does not immediately shrink the `.duckdb` file size on disk due to how DuckDB manages storage.

## Remaining TODOs
- [ ] Implement support for compressed log files (.gz, .zip).
- [ ] Add support for CSV log formats with customizable headers.
- [ ] Enhance Sigma engine with more modifiers (`startswith`, `endswith`, `re`).
- [ ] Implement user authentication and multi-tenancy.
- [ ] Add real-time log tailing and visualization.

## Scalability Concerns
- **Single-Node Storage**: DuckDB is an embedded database. While extremely fast for analytics, it is limited to a single node. High-concurrency or distributed needs would require migrating to a backend like MotherDuck or a distributed OLAP database.
- **Frontend Performance**: Rendering tables with thousands of security findings can impact browser performance. Virtualized lists or better pagination are recommended for scale.

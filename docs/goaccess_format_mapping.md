# GoAccess Log Format Mapping

LogLens automatically detects the log format during upload. When using the GoAccess analytics provider, these formats are mapped to GoAccess `--log-format` strings.

## Supported Mappings

| LogLens Format | GoAccess Format | Description |
|----------------|-----------------|-------------|
| `apache_access`| `COMBINED`      | NCSA Combined Log Format |
| `nginx_access` | `COMBINED`      | NCSA Combined Log Format |
| `clf`          | `COMMON`        | NCSA Common Log Format |
| `iis_w3c`      | `W3C`           | W3C Extended Log Format |

## Default Behavior

If the LogLens format is not explicitly mapped, it defaults to `COMBINED`.

## Fallback Behavior

If GoAccess fails to process the log file with the mapped format, LogLens automatically falls back to the `NativeAnalyticsProvider` (DuckDB), which uses its own internal parsing logic.

## Limitations

- GoAccess might require additional configuration for some custom formats which are currently not supported via the pluggable provider.
- Error logs (Apache, Nginx) are better handled by the Native provider as GoAccess is primarily designed for access logs.

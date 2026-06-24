# External Analytics Evaluation

This document evaluates several external log analytics engines to determine the best fit for LogLens integration.

## Candidates

1. **GoAccess**
2. **Elastic Stack (ELK)**
3. **OpenSearch**
4. **Wazuh**
5. **Loki (Grafana Stack)**

## Comparison Matrix

| Feature | GoAccess | Elastic Stack | OpenSearch | Wazuh | Loki |
|---------|----------|---------------|------------|-------|------|
| **Maintainability** | High | Medium | Medium | Medium | Medium |
| **Upgradeability** | High | Medium | Medium | Medium | High |
| **Resource Usage** | Low (C) | High (Java) | High (Java) | High | Medium (Go) |
| **Dataset Isolation** | High (Process-based) | High (Index-based) | High (Index-based) | High | High (Label-based) |
| **Multi-format Support**| Excellent | Excellent | Excellent | Excellent | Good |
| **Security Focus** | Medium | High | High | Very High | Medium |
| **Ease of Integration** | Very High (JSON) | Medium (API) | Medium (API) | Low (Complex) | Medium (API) |
| **Air-gapped Suitability**| Excellent | Medium | Medium | Medium | High |
| **Longevity** | Very High | Very High | High | High | High |

## Detailed Evaluation

### GoAccess
GoAccess is a real-time web log analyzer and interactive viewer that runs in a terminal or through a browser. It is written in C and is extremely fast and lightweight.
- **Pros:** Minimal dependencies, easy to integrate via JSON export, supports nearly all log formats, perfect for air-gapped environments.
- **Cons:** Primary focus is web logs, though it can be adapted.

### Elastic Stack / OpenSearch
These are the industry standard for log management.
- **Pros:** Unmatched power, scalability, and visualization capabilities.
- **Cons:** Extremely resource-intensive. Requiring a full ELK/OpenSearch stack would significantly increase the footprint of LogLens, potentially making it unusable for smaller environments or single-server deployments.

### Wazuh
A security-focused platform built on OpenSearch.
- **Pros:** Excellent for security monitoring, rule-based detection.
- **Cons:** Very complex to integrate and maintain. Overkill if the goal is general log analytics plus some Sigma rules.

### Loki
Loki is a horizontally-scalable, highly-available, multi-tenant log aggregation system inspired by Prometheus.
- **Pros:** More lightweight than Elasticsearch, great integration with Grafana.
- **Cons:** Requires a whole Grafana ecosystem for the best experience.

## Recommendation: GoAccess

**GoAccess is the recommended external analytics engine for LogLens.**

### Rationale:
1. **Lightweight and Fast:** LogLens currently uses DuckDB, which is also lightweight and fast. GoAccess complements this architecture without introducing heavy Java-based dependencies.
2. **Ease of Integration:** GoAccess provides a comprehensive JSON export that can be easily mapped to LogLens' internal models.
3. **Maintainability:** GoAccess is a mature, stable, and actively maintained project. Using it reduces the custom logic LogLens needs to maintain.
4. **Air-gapped Support:** In many secure environments where LogLens might be deployed, a single binary or a small set of dependencies is preferred over a complex distributed system like Elastic Stack.
5. **Dataset Isolation:** We can easily run GoAccess against specific log files associated with a `upload_id` to maintain strict isolation.

## Implementation Plan for GoAccess Integration
1. Implement a `GoAccessAnalyticsProvider` that executes the `goaccess` binary.
2. Use the `--output=json` flag to retrieve analytics.
3. Map the GoAccess JSON output to the existing `AnalyticsEngine` response structures to ensure frontend compatibility.
4. Maintain the `NativeAnalyticsProvider` (DuckDB-based) as a fallback.

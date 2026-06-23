# Future Roadmap

## Extension Points

### Wazuh Connector
Integrate LogLens with Wazuh to combine web server analytics with host-based intrusion detection (HIDS).
- Pull alerts from Wazuh API.
- Correlate web log activity with system-level security events (e.g., file integrity changes, suspicious processes).
- Display Wazuh alerts in a dedicated "System Security" tab.

### Suricata Connector
Integrate with Suricata for network-based intrusion detection (NIDS).
- Ingest Suricata EVE JSON logs.
- Correlate network flow data with application-level web logs.
- Map network-level threats to specific web sessions.

### AI-Powered Insights
Leverage Large Language Models (LLMs) to provide natural language summaries of log activity.
- "What caused the traffic spike at 10 AM?"
- "Explain why this IP was flagged as suspicious."
- Automated root cause analysis for 5xx error spikes.

### Real-Time Alerting
Implement a webhook-based alerting system.
- Define thresholds for error rates or security findings.
- Send alerts to Slack, Discord, or PagerDuty when rules are triggered.

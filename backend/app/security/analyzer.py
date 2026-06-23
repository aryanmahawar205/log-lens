from typing import Dict, Any, List, Optional
from app.storage.base import BaseStorage
from app.analytics.query_builder import QueryBuilder
from app.security.sigma_engine import SigmaEngine
from app.models.schema import SecurityFinding

class SecurityAnalyzer:
    """
    Analyzes normalized logs to detect security threats and generate risk scores.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.sigma_engine = SigmaEngine()

    def _detect_brute_force(self, where_clause: str, params: tuple, upload_id: int) -> List[Dict[str, Any]]:
        query = f"""
            SELECT ip, url as target_endpoint, COUNT(*) as attempt_count,
                   SUM(CASE WHEN status_code = 401 THEN 1 ELSE 0 END) as failed_logins,
                   MIN(timestamp) as first_seen
            FROM log_entries
            {where_clause}
            AND (url ILIKE '%login%' OR url ILIKE '%signin%' OR url ILIKE '%auth%')
            GROUP BY ip, url
            HAVING COUNT(*) > 10 OR SUM(CASE WHEN status_code = 401 THEN 1 ELSE 0 END) > 5
        """
        results = self.storage.execute_query(query, params)
        findings = []
        for r in results:
            findings.append({
                "rule_id": "custom_brute_force",
                "rule_title": "Brute Force Attempt",
                "severity": "high" if r["failed_logins"] > 20 or r["attempt_count"] > 50 else "medium",
                "dataset_id": upload_id,
                "timestamp": r["first_seen"],
                "ip": r["ip"],
                "evidence": [f"{r['failed_logins']} failed logins, {r['attempt_count']} total attempts on {r['target_endpoint']}"]
            })
        return findings

    def _detect_directory_enumeration(self, where_clause: str, params: tuple, upload_id: int) -> List[Dict[str, Any]]:
        query = f"""
            SELECT ip, COUNT(DISTINCT url) as unique_paths, COUNT(*) as total_requests,
                   SUM(CASE WHEN status_code = 404 THEN 1 ELSE 0 END) as not_found_count,
                   MIN(timestamp) as first_seen
            FROM log_entries
            {where_clause}
            AND (
                url ILIKE '%/admin%' OR url ILIKE '%/.git%' OR url ILIKE '%/.env%'
                OR url ILIKE '%/backup%' OR url ILIKE '%/config%' OR url ILIKE '%/phpmyadmin%'
            )
            GROUP BY ip
            HAVING COUNT(*) > 5
        """
        results = self.storage.execute_query(query, params)
        findings = []
        for r in results:
            findings.append({
                "rule_id": "custom_directory_enumeration",
                "rule_title": "Directory Enumeration",
                "severity": "high" if r["unique_paths"] > 10 or r["not_found_count"] > 20 else "medium",
                "dataset_id": upload_id,
                "timestamp": r["first_seen"],
                "ip": r["ip"],
                "evidence": [f"Probed {r['unique_paths']} sensitive paths, {r['not_found_count']} 404s"]
            })
        return findings

    def _detect_sqli(self, where_clause: str, params: tuple, upload_id: int) -> List[Dict[str, Any]]:
        query = f"""
            SELECT ip, url, query_string, timestamp
            FROM log_entries
            {where_clause}
            AND (
                url ILIKE '%UNION SELECT%' OR query_string ILIKE '%UNION SELECT%' OR
                url ILIKE '%UNION%20SELECT%' OR query_string ILIKE '%UNION%20SELECT%' OR
                url ILIKE '%OR 1=1%' OR query_string ILIKE '%OR 1=1%' OR
                url ILIKE '%OR%201=1%' OR query_string ILIKE '%OR%201=1%' OR
                url ILIKE '%information_schema%' OR query_string ILIKE '%information_schema%' OR
                url ILIKE '%sleep(%' OR query_string ILIKE '%sleep(%' OR
                url ILIKE '%benchmark(%' OR query_string ILIKE '%benchmark(%'
            )
        """
        results = self.storage.execute_query(query, params)
        findings = []
        for r in results:
            evidence_str = f"URL: {r['url']}"
            if r['query_string']:
                evidence_str += f", Query: {r['query_string']}"
            findings.append({
                "rule_id": "custom_sqli",
                "rule_title": "SQL Injection Attempt",
                "severity": "critical",
                "dataset_id": upload_id,
                "timestamp": r["timestamp"],
                "ip": r["ip"],
                "evidence": [evidence_str]
            })
        return findings

    def _detect_xss(self, where_clause: str, params: tuple, upload_id: int) -> List[Dict[str, Any]]:
        query = f"""
            SELECT ip, url, query_string, timestamp
            FROM log_entries
            {where_clause}
            AND (
                url ILIKE '%<script>%' OR query_string ILIKE '%<script>%' OR
                url ILIKE '%javascript:%' OR query_string ILIKE '%javascript:%' OR
                url ILIKE '%onerror=%' OR query_string ILIKE '%onerror=%' OR
                url ILIKE '%alert(%' OR query_string ILIKE '%alert(%' OR
                url ILIKE '%%3Cscript%3E%' OR query_string ILIKE '%%3Cscript%3E%'
            )
        """
        results = self.storage.execute_query(query, params)
        findings = []
        for r in results:
            evidence_str = f"URL: {r['url']}"
            if r['query_string']:
                evidence_str += f", Query: {r['query_string']}"
            findings.append({
                "rule_id": "custom_xss",
                "rule_title": "Cross-Site Scripting Attempt",
                "severity": "high",
                "dataset_id": upload_id,
                "timestamp": r["timestamp"],
                "ip": r["ip"],
                "evidence": [evidence_str]
            })
        return findings

    def _detect_scanners(self, where_clause: str, params: tuple, upload_id: int) -> List[Dict[str, Any]]:
        query = f"""
            SELECT ip, user_agent, COUNT(*) as request_count, MIN(timestamp) as first_seen
            FROM log_entries
            {where_clause}
            AND (
                user_agent ILIKE '%Nikto%' OR
                user_agent ILIKE '%Nmap%' OR
                user_agent ILIKE '%Gobuster%' OR
                user_agent ILIKE '%DirBuster%' OR
                user_agent ILIKE '%sqlmap%' OR
                user_agent ILIKE '%ffuf%' OR
                user_agent ILIKE '%wfuzz%' OR
                user_agent ILIKE '%masscan%' OR
                user_agent ILIKE '%ZMap%' OR
                user_agent ILIKE '%OpenVAS%'
            )
            GROUP BY ip, user_agent
        """
        results = self.storage.execute_query(query, params)
        findings = []
        for r in results:
            findings.append({
                "rule_id": "custom_scanner",
                "rule_title": "Security Scanner Detected",
                "severity": "medium",
                "dataset_id": upload_id,
                "timestamp": r["first_seen"],
                "ip": r["ip"],
                "evidence": [f"Scanner UA: {r['user_agent']}, requests: {r['request_count']}"]
            })
        return findings

    def _detect_command_injection(self, where_clause: str, params: tuple, upload_id: int) -> List[Dict[str, Any]]:
        query = f"""
            SELECT ip, url, query_string, timestamp
            FROM log_entries
            {where_clause}
            AND (
                url ILIKE '%wget %' OR query_string ILIKE '%wget %' OR
                url ILIKE '%curl %' OR query_string ILIKE '%curl %' OR
                url ILIKE '%cat %' OR query_string ILIKE '%cat %' OR
                url ILIKE '%ls %' OR query_string ILIKE '%ls %' OR
                url ILIKE '%;%' OR query_string ILIKE '%;%' OR
                url ILIKE '%|%' OR query_string ILIKE '%|%' OR
                url ILIKE '%&&%' OR query_string ILIKE '%&&%'
            )
        """
        results = self.storage.execute_query(query, params)
        findings = []
        for r in results:
            evidence_str = f"URL: {r['url']}"
            if r['query_string']:
                evidence_str += f", Query: {r['query_string']}"
            findings.append({
                "rule_id": "custom_command_injection",
                "rule_title": "Command Injection Attempt",
                "severity": "critical",
                "dataset_id": upload_id,
                "timestamp": r["timestamp"],
                "ip": r["ip"],
                "evidence": [f"Potential command injection detected in {evidence_str}"]
            })
        return findings

    def _detect_path_traversal(self, where_clause: str, params: tuple, upload_id: int) -> List[Dict[str, Any]]:
        query = f"""
            SELECT ip, url, query_string, timestamp
            FROM log_entries
            {where_clause}
            AND (
                url ILIKE '%../%' OR query_string ILIKE '%../%' OR
                url ILIKE '%%2e%2e%2f%' OR query_string ILIKE '%%2e%2e%2f%' OR
                url ILIKE '%%2e%2e/%' OR query_string ILIKE '%%2e%2e/%' OR
                url ILIKE '%..%2f%' OR query_string ILIKE '%%..%2f%'
            )
        """
        results = self.storage.execute_query(query, params)
        findings = []
        for r in results:
            evidence_str = f"URL: {r['url']}"
            if r['query_string']:
                evidence_str += f", Query: {r['query_string']}"
            findings.append({
                "rule_id": "custom_path_traversal",
                "rule_title": "Path Traversal Attempt",
                "severity": "high",
                "dataset_id": upload_id,
                "timestamp": r["timestamp"],
                "ip": r["ip"],
                "evidence": [f"Path traversal sequence detected in {evidence_str}"]
            })
        return findings

    def get_findings(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get all security findings based on current filters.
        """
        if filters is None:
            filters = {}

        where_condition, params = QueryBuilder.build_filters(filters)
        upload_id = filters.get("upload_id", 0)

        # Adjust where clause structure for queries
        if where_condition:
            where_condition = where_condition # Starts with ' WHERE '
        else:
            where_condition = " WHERE 1=1 "

        findings = []
        findings.extend(self._detect_brute_force(where_condition, tuple(params), upload_id))
        findings.extend(self._detect_directory_enumeration(where_condition, tuple(params), upload_id))
        findings.extend(self._detect_sqli(where_condition, tuple(params), upload_id))
        findings.extend(self._detect_xss(where_condition, tuple(params), upload_id))
        findings.extend(self._detect_scanners(where_condition, tuple(params), upload_id))
        findings.extend(self._detect_command_injection(where_condition, tuple(params), upload_id))
        findings.extend(self._detect_path_traversal(where_condition, tuple(params), upload_id))

        # Add Sigma findings
        sigma_findings = self.sigma_engine.execute(self.storage, filters)
        findings.extend(sigma_findings)

        return findings

    def get_suspicious_ips(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Calculate risk score for all IPs with findings.
        """
        findings = self.get_findings(filters)

        ip_stats = {}
        for finding in findings:
            ip = finding['ip']
            if ip not in ip_stats:
                ip_stats[ip] = {
                    'ip': ip,
                    'score': 0,
                    'critical_count': 0,
                    'high_count': 0,
                    'medium_count': 0,
                    'low_count': 0,
                    'attack_signatures': set(),
                    'findings': []
                }

            stats = ip_stats[ip]
            sev = finding.get('severity', 'low')

            if sev == 'critical':
                stats['score'] += 40
                stats['critical_count'] += 1
            elif sev == 'high':
                stats['score'] += 25
                stats['high_count'] += 1
            elif sev == 'medium':
                stats['score'] += 10
                stats['medium_count'] += 1
            else:
                stats['score'] += 5
                stats['low_count'] += 1

            stats['attack_signatures'].add(finding.get('rule_title', finding.get('type', 'unknown')))
            stats['findings'].append(finding)

        # Cap score at 100, calculate classification
        results = []
        for ip, stats in ip_stats.items():
            stats['risk_score'] = min(100, stats['score'])

            if stats['risk_score'] >= 80:
                stats['severity'] = 'critical'
            elif stats['risk_score'] >= 50:
                stats['severity'] = 'high'
            elif stats['risk_score'] >= 20:
                stats['severity'] = 'medium'
            else:
                stats['severity'] = 'low'

            stats['signatures'] = list(stats['attack_signatures'])
            results.append(stats)

        # Sort by highest score first
        return sorted(results, key=lambda x: x['risk_score'], reverse=True)

    def get_overview(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get high-level security overview for dashboard cards.
        """
        findings = self.get_findings(filters)
        suspicious_ips = self.get_suspicious_ips(filters)

        total_attacks = len(findings)

        severity_dist = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        type_dist = {}

        for f in findings:
            severity = f.get('severity', 'low')
            severity_dist[severity] = severity_dist.get(severity, 0) + 1

            attack_type = f.get('rule_title', f.get('type', 'unknown'))
            type_dist[attack_type] = type_dist.get(attack_type, 0) + 1

        risk_dist = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for ip in suspicious_ips:
            cls = ip.get('severity', 'low')
            risk_dist[cls] = risk_dist.get(cls, 0) + 1

        return {
            "total_attacks": total_attacks,
            "suspicious_ips_count": len(suspicious_ips),
            "severity_distribution": [{"name": k, "value": v} for k, v in severity_dist.items() if v > 0],
            "attack_categories": [{"name": k, "value": v} for k, v in type_dist.items()],
            "risk_distribution": [{"name": k, "value": v} for k, v in risk_dist.items() if v > 0]
        }

    def get_attack_trends(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate timeline of attacks.
        Currently maps to total requests of attackers over time as proxy for attack time.
        In a real implementation we would log timestamp with finding.
        For now, we will query log_entries for timestamps of attacker IPs.
        """
        suspicious_ips = self.get_suspicious_ips(filters)
        if not suspicious_ips:
            return []

        ips = [ip['ip'] for ip in suspicious_ips]

        if filters is None:
            filters = {}
        where_condition, params = QueryBuilder.build_filters(filters)
        if where_condition:
            where_condition += f" AND ip IN ({','.join(['?']*len(ips))})"
        else:
            where_condition = f" WHERE ip IN ({','.join(['?']*len(ips))})"

        # Time bucketing
        query = f"""
            SELECT DATE_TRUNC('hour', timestamp) as time_bucket, COUNT(*) as attack_volume
            FROM log_entries
            {where_condition}
            GROUP BY time_bucket
            ORDER BY time_bucket ASC
        """

        results = self.storage.execute_query(query, tuple(params) + tuple(ips))

        # Format for charts
        return [
            {
                "timestamp": str(r["time_bucket"]),
                "attacks": r["attack_volume"]
            }
            for r in results
        ]

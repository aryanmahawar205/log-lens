import os
import yaml
from typing import List, Dict, Any, Optional
from app.storage.base import BaseStorage

class SigmaEngine:
    """
    Minimalist Sigma execution engine that converts Sigma rules to SQL.
    """

    def __init__(self, rules_path: str = "rules/sigma"):
        self.rules_path = rules_path
        self.rules = []
        self.load_rules()

    def load_rules(self):
        self.rules = []
        if not os.path.exists(self.rules_path):
            return

        for filename in os.listdir(self.rules_path):
            if filename.endswith(".yml") or filename.endswith(".yaml"):
                with open(os.path.join(self.rules_path, filename), "r") as f:
                    try:
                        rule = yaml.safe_load(f)
                        if rule:
                            self.rules.append(rule)
                    except Exception as e:
                        print(f"Error loading Sigma rule {filename}: {e}")

    def get_rules(self) -> List[Dict[str, Any]]:
        return self.rules

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        for rule in self.rules:
            if rule.get("id") == rule_id:
                return rule
        return None

    def _convert_sigma_to_sql(self, rule: Dict[str, Any]) -> Optional[str]:
        """
        Converts a simple Sigma rule to a WHERE clause for DuckDB.
        Supports selection with 'contains' modifier.
        """
        detection = rule.get("detection")
        if not detection:
            return None

        selection = detection.get("selection")
        if not selection:
            return None

        clauses = []
        for field_spec, values in selection.items():
            if "|" in field_spec:
                field, modifier = field_spec.split("|", 1)
            else:
                field, modifier = field_spec, None

            if not isinstance(values, list):
                values = [values]

            field_clauses = []
            for val in values:
                if modifier == "contains":
                    field_clauses.append(f"{field} ILIKE '%{val}%'")
                else:
                    field_clauses.append(f"{field} = '{val}'")

            if field_clauses:
                clauses.append("(" + " OR ".join(field_clauses) + ")")

        if not clauses:
            return None

        return " AND ".join(clauses)

    def execute(self, storage: BaseStorage, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        findings = []

        # Build common filter if any
        from app.analytics.query_builder import QueryBuilder
        base_where, base_params = QueryBuilder.build_filters(filters or {})

        for rule in self.rules:
            sigma_where = self._convert_sigma_to_sql(rule)
            if not sigma_where:
                continue

            where_clause = base_where
            if where_clause:
                where_clause += f" AND ({sigma_where})"
            else:
                where_clause = f" WHERE {sigma_where}"

            query = f"""
                SELECT ip, timestamp, url, query_string, upload_id
                FROM log_entries
                {where_clause}
            """

            results = storage.execute_query(query, tuple(base_params))
            for r in results:
                evidence = [f"URL: {r['url']}"]
                if r['query_string']:
                    evidence.append(f"Query: {r['query_string']}")

                findings.append({
                    "rule_id": rule.get("id", "unknown"),
                    "rule_title": rule.get("title", "Unknown Rule"),
                    "severity": rule.get("level", "medium"),
                    "dataset_id": r["upload_id"],
                    "timestamp": r["timestamp"],
                    "ip": r["ip"],
                    "evidence": evidence,
                    "sigma_source": yaml.dump(rule)
                })

        return findings

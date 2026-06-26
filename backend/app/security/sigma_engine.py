import os
import yaml
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.storage.base import BaseStorage

class SigmaEngine:
    """
    Sigma execution engine that converts Sigma rules to SQL.
    Supports basic condition parsing, multiple fields, and contains modifier.
    """

    def __init__(self, rules_path: str = "rules/sigma"):
        self.rules_path = rules_path
        self.rules = []

        # Diagnostics state
        self.last_reload = None
        self.execution_count = 0
        self.last_execution_status = "Not executed"
        self.last_execution_duration = 0.0
        self.last_execution_timestamp = None
        self.last_error = None
        self.failed_rules = []
        self.ignored_rules = []

        self.load_rules()

    def load_rules(self):
        self.rules = []
        self.failed_rules = []
        self.ignored_rules = []

        if not os.path.exists(self.rules_path):
            self.last_error = f"Rules path {self.rules_path} does not exist"
            self.last_reload = datetime.now().isoformat()
            return

        for filename in os.listdir(self.rules_path):
            if filename.endswith(".yml") or filename.endswith(".yaml"):
                with open(os.path.join(self.rules_path, filename), "r") as f:
                    try:
                        rule = yaml.safe_load(f)
                        if rule:
                            # Validate minimum fields
                            if not rule.get("detection"):
                                self.ignored_rules.append(filename)
                                continue

                            rule["filename"] = filename
                            if "status" not in rule:
                                rule["status"] = "experimental" # Default if missing

                            self.rules.append(rule)
                    except Exception as e:
                        print(f"Error loading Sigma rule {filename}: {e}")
                        self.failed_rules.append(filename)

        self.last_reload = datetime.now().isoformat()
        self.last_error = None

    def get_rules(self) -> List[Dict[str, Any]]:
        return self.rules

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        for rule in self.rules:
            if rule.get("id") == rule_id:
                return rule
        return None

    def _convert_selection_to_sql(self, selection: Dict[str, Any]) -> str:
        """
        Converts a single selection map to a SQL string.
        A map is a logical AND of its fields.
        """
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
                # Escape single quotes in SQL
                val_escaped = str(val).replace("'", "''")
                if modifier == "contains":
                    field_clauses.append(f"{field} ILIKE '%{val_escaped}%'")
                elif modifier == "startswith":
                    field_clauses.append(f"{field} ILIKE '{val_escaped}%'")
                elif modifier == "endswith":
                    field_clauses.append(f"{field} ILIKE '%{val_escaped}'")
                else:
                    field_clauses.append(f"{field} = '{val_escaped}'")

            if field_clauses:
                # Logical OR across the list of values for a single field
                clauses.append("(" + " OR ".join(field_clauses) + ")")

        # Logical AND across keys in the map
        if clauses:
            return "(" + " AND ".join(clauses) + ")"
        return "1=1"

    def _convert_list_selection_to_sql(self, selection_list: List[Dict[str, Any]]) -> str:
        """
        Converts a list of selection maps to SQL.
        A list is a logical OR of its elements.
        """
        clauses = []
        for item in selection_list:
            if isinstance(item, dict):
                clauses.append(self._convert_selection_to_sql(item))
        if clauses:
            return "(" + " OR ".join(clauses) + ")"
        return "1=1"

    def _parse_condition(self, condition: str, selections: Dict[str, Any]) -> str:
        """
        Parses the Sigma condition string and builds the final SQL where clause.
        Supports 'or', 'and', 'not', and selection names.
        """
        tokens = condition.replace('(', ' ( ').replace(')', ' ) ').split()
        sql_parts = []

        for token in tokens:
            lower_token = token.lower()
            if lower_token == 'or':
                sql_parts.append('OR')
            elif lower_token == 'and':
                sql_parts.append('AND')
            elif lower_token == 'not':
                sql_parts.append('NOT')
            elif token in ['(', ')']:
                sql_parts.append(token)
            elif lower_token == '1' and 'of' in tokens:
                pass
            elif lower_token == 'of':
                pass
            elif token.startswith('selection') or token.startswith('keywords') or token in selections:
                if token in selections:
                    sel_data = selections[token]
                    if isinstance(sel_data, dict):
                        sql_parts.append(self._convert_selection_to_sql(sel_data))
                    elif isinstance(sel_data, list):
                        sql_parts.append(self._convert_list_selection_to_sql(sel_data))
                elif token.endswith('*'):
                    prefix = token[:-1]
                    matched_clauses = []
                    for k, v in selections.items():
                        if k.startswith(prefix):
                            if isinstance(v, dict):
                                matched_clauses.append(self._convert_selection_to_sql(v))
                            elif isinstance(v, list):
                                matched_clauses.append(self._convert_list_selection_to_sql(v))
                    if matched_clauses:
                        sql_parts.append("(" + " OR ".join(matched_clauses) + ")")
                    else:
                        sql_parts.append("1=0")
            else:
                if token == '*':
                    matched_clauses = []
                    for k, v in selections.items():
                        if isinstance(v, dict):
                            matched_clauses.append(self._convert_selection_to_sql(v))
                        elif isinstance(v, list):
                            matched_clauses.append(self._convert_list_selection_to_sql(v))

                    if 'all' in tokens:
                        sql_parts.append("(" + " AND ".join(matched_clauses) + ")")
                    else:
                        sql_parts.append("(" + " OR ".join(matched_clauses) + ")")

        res = " ".join(sql_parts)
        if not res.strip():
            return "1=1"
        return res

    def _convert_sigma_to_sql(self, rule: Dict[str, Any]) -> Optional[str]:
        detection = rule.get("detection")
        if not detection:
            return None

        condition = detection.get("condition")
        if not condition:
            return None

        selections = {k: v for k, v in detection.items() if k != "condition"}
        return self._parse_condition(condition, selections)

    def execute(self, storage: 'BaseStorage', filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        start_time = time.time()
        findings = []
        execution_id = None
        upload_id = filters.get("upload_id") if filters else 0

        try:
            # Record execution history and get execution ID
            res = storage.execute_query("""
                INSERT INTO external_tool_executions (id, tool_name, upload_id, status, execution_timestamp, duration_sec, version, artifacts)
                VALUES (nextval('seq_execution_id'), 'sigma', ?, 'running', ?, 0, '1.0', '{}')
                RETURNING id
            """, (upload_id if upload_id else 0, datetime.now()))
            if res:
                execution_id = res[0]["id"]

            from app.analytics.query_builder import QueryBuilder
            base_where, base_params = QueryBuilder.build_filters(filters or {})

            for rule in self.rules:
                sigma_where = self._convert_sigma_to_sql(rule)
                if not sigma_where or sigma_where.strip() == "1=1" or sigma_where.strip() == "":
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
                        "sigma_source": yaml.dump(rule),
                        "providers": ["Sigma"],
                        "filename": rule.get("filename"),
                        "status": rule.get("status"),
                        "execution_id": execution_id
                    })

            self.execution_count += 1
            self.last_execution_status = "Success"
            self.last_error = None

            if execution_id:
                storage.execute_query("""
                    UPDATE external_tool_executions
                    SET status = 'success', duration_sec = ?
                    WHERE id = ?
                """, (time.time() - start_time, execution_id))
        except Exception as e:
            self.last_execution_status = "Failed"
            self.last_error = str(e)
            print(f"Sigma engine error: {e}")

            if execution_id:
                import json
                storage.execute_query("""
                    UPDATE external_tool_executions
                    SET status = 'failed', duration_sec = ?, artifacts = ?
                    WHERE id = ?
                """, (time.time() - start_time, json.dumps({"error": str(e)}), execution_id))
        finally:
            self.last_execution_duration = time.time() - start_time
            self.last_execution_timestamp = datetime.now().isoformat()

        return findings

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "provider_status": "active" if self.last_execution_status == "Success" else "error",
            "healthy_state": self.last_error is None,
            "version": "1.0",
            "loaded_rules": len(self.rules),
            "failed_rules": len(self.failed_rules),
            "ignored_rules": len(self.ignored_rules),
            "last_reload": self.last_reload,
            "execution_count": self.execution_count,
            "last_execution_status": self.last_execution_status,
            "execution_duration": self.last_execution_duration,
            "last_execution_timestamp": self.last_execution_timestamp,
            "last_error": self.last_error
        }

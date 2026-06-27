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
        self.last_reload_duration = 0.0
        self.total_discovered_rules = 0
        self.directories_scanned = 0
        self.execution_count = 0
        self.last_execution_status = "Not executed"
        self.last_execution_duration = 0.0
        self.last_execution_timestamp = None
        self.last_error = None
        self.failed_rules = []
        self.ignored_rules = []
        self.duplicate_rules = []

        self.load_rules()

    def load_rules(self):
        start_time = time.time()
        self.rules = []
        self.failed_rules = []
        self.ignored_rules = []
        self.duplicate_rules = []
        self.total_discovered_rules = 0
        self.directories_scanned = 0

        loaded_ids = set()

        if not os.path.exists(self.rules_path):
            self.last_error = f"Rules path {self.rules_path} does not exist"
            self.last_reload = datetime.now().isoformat()
            self.last_reload_duration = time.time() - start_time
            return

        for root, dirs, files in os.walk(self.rules_path):
            self.directories_scanned += 1
            for filename in files:
                if filename.endswith(".yml") or filename.endswith(".yaml"):
                    self.total_discovered_rules += 1
                    filepath = os.path.join(root, filename)
                    # Create a friendly relative path for reporting
                    rel_filepath = os.path.relpath(filepath, self.rules_path)

                    try:
                        with open(filepath, "r") as f:
                            rule = yaml.safe_load(f)
                            if rule:
                                # Validate minimum fields
                                if not rule.get("detection"):
                                    self.ignored_rules.append(rel_filepath)
                                    continue

                                rule_id = rule.get("id")
                                if rule_id:
                                    if rule_id in loaded_ids:
                                        self.duplicate_rules.append(rel_filepath)
                                        self.failed_rules.append(rel_filepath)
                                        continue
                                    loaded_ids.add(rule_id)

                                rule["filename"] = rel_filepath
                                if "status" not in rule:
                                    rule["status"] = "experimental" # Default if missing

                                self.rules.append(rule)
                    except Exception as e:
                        print(f"Error loading Sigma rule {rel_filepath}: {e}")
                        self.failed_rules.append(rel_filepath)

        self.last_reload = datetime.now().isoformat()
        self.last_reload_duration = time.time() - start_time
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

            # Mapping common IIS/Apache fields from sigma rules to DuckDB normalized fields
            if field == "cs-method" or field == "c-method":
                field = "method"
            elif field == "sc-status" or field == "c-status":
                field = "status_code"
            elif field == "cs-user-agent" or field == "c-useragent" or field == "useragent":
                field = "user_agent"
            elif field == "cs-uri-query" or field == "c-uri-query" or field == "uri-query":
                field = "query_string"
            elif field == "cs-uri-stem" or field == "c-uri-stem" or field == "uri-stem":
                field = "url"
            elif field == "c-ip" or field == "cs-ip":
                field = "ip"
            elif field == "cs-referer" or field == "c-referer" or field == "referer":
                field = "referrer"
            elif field == "cs-host" or field == "c-host" or field == "host":
                field = "host"
            elif field == "cs-uri" or field == "c-uri" or field == "uri":
                field = "url"
            elif field == "c-uri-extension" or field == "cs-uri-extension":
                # For basic support, map extension to URL. Ideally would parse it but this allows contains/endswith to work somewhat
                field = "url"
            elif field == "cs-cookie" or field == "c-cookie" or field == "cookie":
                # We don't have a normalized cookie field by default, we can just match it against the raw request line if possible, or query_string as fallback.
                # Actually, this is a proxy log field. If we don't have it, we shouldn't fail the whole query. Let's just map it to user_agent for now as a fallback to avoid crashing or `1=0`.
                field = "user_agent"
            elif field == "dst_ip" or field == "c-dst-ip" or field == "src_ip" or field == "c-src-ip":
                field = "ip"

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
            elif token.startswith('selection') or token.startswith('keywords') or token.startswith('filter') or token in selections:
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
            "total_discovered_rules": self.total_discovered_rules,
            "directories_scanned": self.directories_scanned,
            "loaded_rules": len(self.rules),
            "failed_rules": len(self.failed_rules),
            "ignored_rules": len(self.ignored_rules),
            "duplicate_rules": len(self.duplicate_rules),
            "last_reload": self.last_reload,
            "last_reload_duration": self.last_reload_duration,
            "execution_count": self.execution_count,
            "last_execution_status": self.last_execution_status,
            "execution_duration": self.last_execution_duration,
            "last_execution_timestamp": self.last_execution_timestamp,
            "last_error": self.last_error
        }

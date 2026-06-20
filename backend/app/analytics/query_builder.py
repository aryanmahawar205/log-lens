from typing import Dict, Any, Tuple, List

class QueryBuilder:
    """
    Constructs parameterized WHERE clauses for filtering logs.
    """

    @staticmethod
    def build_filters(filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Builds a SQL WHERE clause and corresponding parameter list.

        Supported filters:
        - start_date (str, iso format)
        - end_date (str, iso format)
        - ip (str)
        - url (str)
        - normalized_url (str)
        - status_code (int)
        - user_agent (str)
        - bot_classification (str)
        """
        if not filters:
            return "", []

        clauses = []
        parameters = []

        if "start_date" in filters and filters["start_date"]:
            clauses.append("timestamp >= CAST(? AS TIMESTAMP)")
            parameters.append(filters["start_date"])

        if "end_date" in filters and filters["end_date"]:
            clauses.append("timestamp <= CAST(? AS TIMESTAMP)")
            parameters.append(filters["end_date"])

        if "ip" in filters and filters["ip"]:
            clauses.append("ip = ?")
            parameters.append(filters["ip"])

        if "url" in filters and filters["url"]:
            clauses.append("url = ?")
            parameters.append(filters["url"])

        if "normalized_url" in filters and filters["normalized_url"]:
            clauses.append("normalized_url = ?")
            parameters.append(filters["normalized_url"])

        if "status_code" in filters and filters["status_code"]:
            clauses.append("status_code = ?")
            parameters.append(filters["status_code"])

        if "user_agent" in filters and filters["user_agent"]:
            # Like query for user agent since it might be a partial match
            clauses.append("user_agent LIKE ?")
            parameters.append(f"%{filters['user_agent']}%")

        if "bot_classification" in filters and filters["bot_classification"]:
            clauses.append("bot_classification = ?")
            parameters.append(filters["bot_classification"])

        if not clauses:
            return "", []

        where_clause = " WHERE " + " AND ".join(clauses)
        return where_clause, parameters

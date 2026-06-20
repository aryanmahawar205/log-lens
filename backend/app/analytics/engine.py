from typing import List, Dict, Any
import polars as pl
from app.models.schema import NormalizedLogEntry

class AnalyticsEngine:
    """
    Core analytics engine using Polars for high-performance log processing.
    """

    def __init__(self):
        self.df = pl.DataFrame()

    def ingest_entries(self, entries: List[NormalizedLogEntry]):
        """
        Ingest a list of NormalizedLogEntry objects into the engine.
        """
        if not entries:
            return

        new_data = [entry.model_dump() for entry in entries]
        new_df = pl.DataFrame(new_data)

        if self.df.is_empty():
            self.df = new_df
        else:
            self.df = pl.concat([self.df, new_df])

    def get_traffic_summary(self) -> Dict[str, Any]:
        """
        Return high-level traffic metrics.
        """
        if self.df.is_empty():
            return {
                "total_requests": 0,
                "total_bytes": 0,
                "unique_visitors": 0
            }

        return {
            "total_requests": len(self.df),
            "total_bytes": int(self.df["bytes_sent"].sum()),
            "unique_visitors": self.df["ip"].n_unique()
        }

    def get_status_code_distribution(self) -> List[Dict[str, Any]]:
        """
        Return the distribution of HTTP status codes.
        """
        if self.df.is_empty():
            return []

        dist = self.df.group_by("status_code").count().sort("count", descending=True)
        return dist.to_dicts()

    def get_top_urls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return the most frequently accessed URLs.
        """
        if self.df.is_empty():
            return []

        top_urls = self.df.group_by("url").count().sort("count", descending=True).head(limit)
        return top_urls.to_dicts()

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class AnalyticsProvider(ABC):
    """
    Abstract base class for analytics providers.
    """

    @abstractmethod
    def get_traffic_summary(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_time_analytics(self, resolution: str = 'hour', filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_performance_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_top_urls(self, limit: int = 10, normalized: bool = False, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_entry_exit_pages(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def get_visitor_analytics(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def get_status_code_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_traffic_trends(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_bounce_and_landing_pages(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        pass

    @abstractmethod
    def get_extended_performance_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_status_code_groups(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_extended_visitor_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

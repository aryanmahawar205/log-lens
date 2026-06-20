from typing import List, Dict, Any, Optional
from datetime import timedelta
import polars as pl
from app.models.schema import NormalizedLogEntry

class Sessionizer:
    """
    Session reconstruction from log entries.
    Groups by IP + User Agent with a configurable timeout (default 30 mins).
    """

    def __init__(self, timeout_minutes: int = 30):
        self.timeout = timedelta(minutes=timeout_minutes)

    def process_sessions(self, entries: List[NormalizedLogEntry]) -> Dict[str, Any]:
        """
        Process entries and return session metrics:
        - sessions count
        - session duration average
        - pages per session average
        - entry pages
        - exit pages
        """
        if not entries:
            return {
                "total_sessions": 0,
                "avg_duration_seconds": 0.0,
                "avg_pages_per_session": 0.0,
                "entry_pages": {},
                "exit_pages": {}
            }

        # Sort entries by timestamp to ensure correct chronological processing
        sorted_entries = sorted(entries, key=lambda e: e.timestamp)

        sessions: Dict[str, List[NormalizedLogEntry]] = {} # key: session_id -> List of entries

        # State tracking for ongoing sessions
        # key: (ip, user_agent) -> {"session_id": str, "last_seen": datetime}
        active_sessions = {}
        session_counter = 0

        for entry in sorted_entries:
            key = (entry.ip, entry.user_agent or "unknown")

            if key in active_sessions:
                last_seen = active_sessions[key]["last_seen"]
                # Check for timeout
                if entry.timestamp - last_seen > self.timeout:
                    # New session
                    session_counter += 1
                    session_id = f"s_{session_counter}"
                    active_sessions[key] = {"session_id": session_id, "last_seen": entry.timestamp}
                else:
                    # Continue session
                    active_sessions[key]["last_seen"] = entry.timestamp
                    session_id = active_sessions[key]["session_id"]
            else:
                # First time seeing this key
                session_counter += 1
                session_id = f"s_{session_counter}"
                active_sessions[key] = {"session_id": session_id, "last_seen": entry.timestamp}

            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(entry)

        # Calculate metrics
        total_sessions = len(sessions)

        if total_sessions == 0:
             return {
                "total_sessions": 0,
                "avg_duration_seconds": 0.0,
                "avg_pages_per_session": 0.0,
                "entry_pages": {},
                "exit_pages": {}
            }

        total_duration_sec = 0.0
        total_pages = 0
        entry_pages: Dict[str, int] = {}
        exit_pages: Dict[str, int] = {}

        for session_id, session_entries in sessions.items():
            # Session entries are already ordered by time because we processed sorted_entries
            start_time = session_entries[0].timestamp
            end_time = session_entries[-1].timestamp

            duration_sec = (end_time - start_time).total_seconds()
            total_duration_sec += duration_sec

            pages = len(session_entries)
            total_pages += pages

            # Entry and Exit pages
            entry_url = session_entries[0].url
            exit_url = session_entries[-1].url

            entry_pages[entry_url] = entry_pages.get(entry_url, 0) + 1
            exit_pages[exit_url] = exit_pages.get(exit_url, 0) + 1

        avg_duration = total_duration_sec / total_sessions if total_sessions > 0 else 0
        avg_pages = total_pages / total_sessions if total_sessions > 0 else 0

        # Sort pages dicts by count desc
        sorted_entry_pages = dict(sorted(entry_pages.items(), key=lambda item: item[1], reverse=True))
        sorted_exit_pages = dict(sorted(exit_pages.items(), key=lambda item: item[1], reverse=True))

        return {
            "total_sessions": total_sessions,
            "avg_duration_seconds": avg_duration,
            "avg_pages_per_session": avg_pages,
            "entry_pages": sorted_entry_pages,
            "exit_pages": sorted_exit_pages
        }

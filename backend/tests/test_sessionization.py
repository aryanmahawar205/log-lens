import pytest
from datetime import datetime, timezone, timedelta
from app.sessionization.sessionizer import Sessionizer
from app.models.schema import NormalizedLogEntry

def create_entry(ip, ua, dt_str, url):
    return NormalizedLogEntry(
        timestamp=datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S'),
        ip=ip,
        method="GET",
        url=url,
        status_code=200,
        bytes_sent=100,
        user_agent=ua
    )

def test_sessionizer():
    entries = [
        create_entry("1.1.1.1", "BrowserA", "2023-01-01 10:00:00", "/home"),
        create_entry("1.1.1.1", "BrowserA", "2023-01-01 10:15:00", "/about"),
        create_entry("2.2.2.2", "BrowserB", "2023-01-01 10:10:00", "/contact"),
        # Timeout for 1.1.1.1 BrowserA
        create_entry("1.1.1.1", "BrowserA", "2023-01-01 11:00:00", "/login"),
    ]

    sessionizer = Sessionizer(timeout_minutes=30)
    metrics = sessionizer.process_sessions(entries)

    assert metrics["total_sessions"] == 3
    # Sessions:
    # 1: 1.1.1.1 BrowserA (10:00 to 10:15 = 15 mins = 900s) -> 2 pages
    # 2: 2.2.2.2 BrowserB (10:10 = 0 mins = 0s) -> 1 page
    # 3: 1.1.1.1 BrowserA (11:00 = 0 mins = 0s) -> 1 page

    # Avg duration = 900 / 3 = 300s
    assert metrics["avg_duration_seconds"] == 300.0

    # Avg pages = 4 pages / 3 sessions
    assert metrics["avg_pages_per_session"] == 4.0 / 3.0

    # Entry pages: /home (1), /contact (1), /login (1)
    assert metrics["entry_pages"]["/home"] == 1
    assert metrics["entry_pages"]["/contact"] == 1
    assert metrics["entry_pages"]["/login"] == 1

    # Exit pages: /about (1), /contact (1), /login (1)
    assert metrics["exit_pages"]["/about"] == 1

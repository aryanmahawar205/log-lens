from fastapi import FastAPI
from app.api.routes import security, analytics
from fastapi.middleware.cors import CORSMiddleware
from app.storage.duckdb_storage import DuckDBStorage
from app.parsers.clf import CLFParser
from app.models.schema import NormalizedLogEntry
from datetime import datetime
import uvicorn
import threading

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

db = DuckDBStorage("data/analytics.duckdb")
# Hacky inject test data
entries = [
    NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/admin", status_code=404, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/.git", status_code=404, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/.env", status_code=404, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/backup", status_code=404, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/config", status_code=404, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="192.168.1.100", method="GET", url="/phpmyadmin", status_code=404, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.5", method="POST", url="/login", status_code=401, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.10", method="GET", url="/product", query_string="id=1%20UNION%20SELECT", status_code=200, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="172.16.0.10", method="GET", url="/search", query_string="q=%3Cscript%3Ealert(1)%3C/script%3E", status_code=200, bytes_sent=0, user_agent="Mozilla"),
    NormalizedLogEntry(timestamp=datetime.now(), ip="10.0.0.99", method="GET", url="/", status_code=200, bytes_sent=0, user_agent="sqlmap/1.5.8")
]
db.ingest_batch(entries)

analytics.storage = db
security.storage = db

app.include_router(analytics.router, prefix="/api/v1/analytics")
app.include_router(security.router, prefix="/api/v1/analytics/security")

uvicorn.run(app, host="0.0.0.0", port=8000)

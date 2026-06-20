from fastapi import APIRouter, HTTPException, UploadFile, File
from app.analytics.engine import AnalyticsEngine
from app.parsers.apache import ApacheAccessParser
import tempfile
import os

router = APIRouter()

# In a real app, this would be a persistent singleton or database-backed
analytics_engine = AnalyticsEngine()
parser = ApacheAccessParser()

@router.post("/upload")
async def upload_log_file(file: UploadFile = File(...)):
    """
    Upload a log file for analysis. Currently supports Apache format.
    """
    tmp_path = None
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Parse and ingest
        entries = list(parser.parse_file(tmp_path))
        analytics_engine.ingest_entries(entries)

        return {"message": f"Successfully ingested {len(entries)} log entries"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.get("/summary")
async def get_summary():
    """
    Get high-level traffic summary.
    """
    return analytics_engine.get_traffic_summary()

@router.get("/status-codes")
async def get_status_codes():
    """
    Get HTTP status code distribution.
    """
    return analytics_engine.get_status_code_distribution()

@router.get("/top-urls")
async def get_top_urls():
    """
    Get top accessed URLs.
    """
    return analytics_engine.get_top_urls()

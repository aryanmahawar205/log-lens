from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Depends
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.analytics.engine import NativeAnalyticsProvider
from app.analytics.goaccess import GoAccessAnalyticsProvider
from app.parsers.detector import FormatDetector
from app.parsers.registry import ParserRegistry
from app.config import config

import tempfile
import os

router = APIRouter()

# Persistent singleton mapped to DuckDB
from app.storage.duckdb_storage import DuckDBStorage

os.makedirs("data", exist_ok=True)
storage = DuckDBStorage("data/analytics.duckdb")

# Analytics Provider Selection with Fallback
native_provider = NativeAnalyticsProvider(storage=storage)
provider_type = config.get("analytics.provider", "native")

if provider_type == "goaccess":
    analytics_engine = GoAccessAnalyticsProvider(
        storage=storage,
        fallback_provider=native_provider
    )
else:
    analytics_engine = native_provider

from datetime import datetime

def get_filters(
    upload_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    ip: Optional[str] = Query(None),
    url: Optional[str] = Query(None),
    normalized_url: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    user_agent: Optional[str] = Query(None),
    bot_classification: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Dependency to extract common filters from query parameters."""
    return {
        "upload_id": upload_id,
        "start_date": start_date,
        "end_date": end_date,
        "ip": ip,
        "url": url,
        "normalized_url": normalized_url,
        "status_code": status_code,
        "user_agent": user_agent,
        "bot_classification": bot_classification
    }

@router.get("/datasets")
async def get_datasets():
    """Get all available datasets (uploads)."""
    return storage.execute_query("SELECT * FROM uploads ORDER BY uploaded_at DESC")

@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: int):
    """Get a specific dataset."""
    result = storage.execute_query("SELECT * FROM uploads WHERE id = ?", (dataset_id,))
    if not result:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return result[0]

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: int):
    """Delete a dataset and its logs."""
    storage.execute_query("DELETE FROM log_entries WHERE upload_id = ?", (dataset_id,))
    storage.execute_query("DELETE FROM uploads WHERE id = ?", (dataset_id,))
    return {"message": "Dataset deleted successfully"}

@router.delete("/reset")
async def reset_database():
    """Reset the database for testing and validation."""
    storage.execute_query("DELETE FROM log_entries")
    storage.execute_query("DELETE FROM uploads")
    return {"message": "Database reset successfully"}

async def process_log_file(file_path: str, original_filename: str, original_path: str = None, file_size: int = None, checksum: str = None, last_modified: datetime = None) -> Dict[str, Any]:
    """
    Shared logic to detect format, parse, and ingest a log file into the database.
    """
    # Detect format
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        sample_lines = [line.strip() for line in f.readlines(8192) if line.strip()][:100]

    format_name, confidence = FormatDetector.detect_format(sample_lines)
    if not format_name:
        raise ValueError("Could not detect log format.")

    parser = ParserRegistry.get_parser(format_name)
    if not parser:
        raise ValueError(f"Parser {format_name} not found.")

    # Generate new upload ID (Unix timestamp or sequence)
    upload_id = int(datetime.now().timestamp() * 1000)

    # For GoAccess or other external tools, we may want to preserve the raw log file
    raw_log_dir = "data/raw_logs"
    os.makedirs(raw_log_dir, exist_ok=True)

    raw_log_path = os.path.join(raw_log_dir, f"{upload_id}.log")
    import shutil
    if file_path != raw_log_path:
        shutil.copy(file_path, raw_log_path)

    # Parse and ingest in batches to minimize memory footprint
    batch_size = 10000
    current_batch = []
    total_ingested = 0

    # We still ingest into Native provider for secondary analytics and log exploration
    # even if GoAccess is primary for overview
    for entry in parser.parse_file(file_path):
        current_batch.append(entry)
        if len(current_batch) >= batch_size:
            storage.ingest_batch(current_batch, upload_id)
            total_ingested += len(current_batch)
            current_batch.clear()

    # Ingest remaining
    if current_batch:
        storage.ingest_batch(current_batch, upload_id)
        total_ingested += len(current_batch)

    # Record upload in uploads table
    storage.execute_query("""
        INSERT INTO uploads (id, filename, format, uploaded_at, total_entries, parser_used, confidence, original_path, file_size, checksum, last_modified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (upload_id, original_filename, format_name, datetime.now(), total_ingested, format_name, confidence, original_path, file_size, checksum, last_modified))

    return {
        "message": f"Successfully ingested {total_ingested} log entries",
        "upload_id": upload_id,
        "format": format_name,
        "confidence": confidence
    }

class FolderImportRequest(BaseModel):
    folder_path: str

@router.post("/upload/folder")
async def upload_folder(request: FolderImportRequest):
    """
    Recursively scan a directory, discover supported logs, skip duplicates, and import them.
    """
    folder_path = request.folder_path
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="Invalid directory path")

    import hashlib
    def compute_checksum(filepath: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    existing_checksums = {row['checksum'] for row in storage.execute_query("SELECT checksum FROM uploads WHERE checksum IS NOT NULL")}

    files_discovered = 0
    files_imported = 0
    files_skipped = 0
    files_unsupported = 0
    start_time = datetime.now()

    scan_id = int(start_time.timestamp() * 1000)

    for root, _, files in os.walk(folder_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            files_discovered += 1

            # Get basic metadata
            try:
                stat = os.stat(filepath)
                file_size = stat.st_size
                last_modified = datetime.fromtimestamp(stat.st_mtime)
            except Exception:
                files_skipped += 1
                continue

            checksum = compute_checksum(filepath)

            # Duplicate check
            if checksum in existing_checksums:
                files_skipped += 1
                continue

            # Try processing
            try:
                # We attempt to process it; if process_log_file raises ValueError, it's unsupported
                await process_log_file(
                    file_path=filepath,
                    original_filename=filename,
                    original_path=filepath,
                    file_size=file_size,
                    checksum=checksum,
                    last_modified=last_modified
                )
                files_imported += 1
                existing_checksums.add(checksum)
            except ValueError:
                files_unsupported += 1
            except Exception as e:
                # Other errors during processing
                print(f"Error processing {filepath}: {e}")
                files_skipped += 1

    duration = (datetime.now() - start_time).total_seconds()
    status = "SUCCESS" if files_imported > 0 else "COMPLETED_NO_IMPORTS"

    storage.execute_query("""
        INSERT INTO folder_scans (id, folder_path, scanned_at, files_discovered, files_imported, files_skipped, files_unsupported, duration_sec, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (scan_id, folder_path, start_time, files_discovered, files_imported, files_skipped, files_unsupported, duration, status))

    return {
        "message": f"Folder scan completed. Imported {files_imported} new files.",
        "details": {
            "files_discovered": files_discovered,
            "files_imported": files_imported,
            "files_skipped": files_skipped,
            "files_unsupported": files_unsupported,
            "duration_sec": duration,
            "status": status
        }
    }

@router.post("/upload")
async def upload_log_file(file: UploadFile = File(...)):
    """
    Upload a log file for analysis. Detects format and streams batches into the database.
    """
    tmp_path = None
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # For extremely large files this should use chunked reading
            # but for our use case we write it down first to use streaming ingestion tools.
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        import hashlib
        # Compute basic checksum for UI-uploaded files if we want, but not strictly necessary here.
        # Just passing None for now.

        result = await process_log_file(tmp_path, file.filename)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.get("/overview")
async def get_overview(filters: dict = Depends(get_filters)):
    """
    Get high-level traffic overview combining traffic and visitor statistics.
    """
    summary = analytics_engine.get_traffic_summary(filters)
    return summary

@router.get("/traffic")
async def get_traffic(resolution: str = Query('hour'), filters: dict = Depends(get_filters)):
    """
    Get time-series traffic analytics.
    """
    return analytics_engine.get_time_analytics(resolution, filters)

@router.get("/performance")
async def get_performance(filters: dict = Depends(get_filters)):
    """
    Get performance analytics including response times and slow endpoints.
    """
    return analytics_engine.get_performance_analytics(filters)

@router.get("/urls")
async def get_urls(limit: int = Query(10), normalized: bool = Query(False), filters: dict = Depends(get_filters)):
    """
    Get URL analytics including top pages and entry/exit points.
    """
    top_urls = analytics_engine.get_top_urls(limit, normalized, filters)
    entry_exit = analytics_engine.get_entry_exit_pages(limit, filters)

    return {
        "top_urls": top_urls,
        "entry_pages": entry_exit["entry_pages"],
        "exit_pages": entry_exit["exit_pages"]
    }

@router.get("/visitors")
async def get_visitors(limit: int = Query(10), filters: dict = Depends(get_filters)):
    """
    Get visitor analytics including IPs and User Agents.
    """
    return analytics_engine.get_visitor_analytics(limit, filters)

@router.get("/status-codes")
async def get_status_codes(filters: dict = Depends(get_filters)):
    """
    Get HTTP status code distribution and success/error rates.
    """
    return analytics_engine.get_status_code_analytics(filters)

@router.get("/traffic/trends")
async def get_traffic_trends(filters: dict = Depends(get_filters)):
    """Get traffic trends including moving averages and growth."""
    return analytics_engine.get_traffic_trends(filters)

@router.get("/urls/landing-bounce")
async def get_landing_bounce(limit: int = Query(10), filters: dict = Depends(get_filters)):
    """Get landing pages and bounce candidates."""
    return analytics_engine.get_bounce_and_landing_pages(limit, filters)

@router.get("/performance/extended")
async def get_performance_extended(filters: dict = Depends(get_filters)):
    """Get extended performance metrics (fastest endpoints, throughput)."""
    return analytics_engine.get_extended_performance_analytics(filters)

@router.get("/status-codes/groups")
async def get_status_code_groups(filters: dict = Depends(get_filters)):
    """Get status codes grouped by endpoint, hour, and day."""
    return analytics_engine.get_status_code_groups(filters)

@router.get("/visitors/extended")
async def get_visitors_extended(filters: dict = Depends(get_filters)):
    """Get extended visitor analytics (browser and OS distribution)."""
    return analytics_engine.get_extended_visitor_analytics(filters)

@router.get("/logs")
async def get_logs(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("timestamp"),
    sort_desc: bool = Query(True),
    filters: dict = Depends(get_filters)
):
    """
    Raw log explorer endpoint with pagination, filtering and sorting.
    """

    allowed_columns = {
        "timestamp",
        "ip",
        "method",
        "status_code",
        "url",
        "response_time_ms"
    }

    if sort_by not in allowed_columns:
        sort_by = "timestamp"

    order = "DESC" if sort_desc else "ASC"

    from app.analytics.query_builder import QueryBuilder
    where_sql, params = QueryBuilder.build_filters(filters)

    query = f"""
        SELECT
            timestamp,
            ip,
            method,
            status_code,
            url,
            response_time_ms,
            user_agent
        FROM log_entries
        {where_sql}
        ORDER BY {sort_by} {order}
        LIMIT ?
        OFFSET ?
    """

    rows = storage.execute_query(
        query,
        tuple(params + [limit, offset])
    )

    count_query = f"""
        SELECT COUNT(*) as total
        FROM log_entries
        {where_sql}
    """

    total_result = storage.execute_query(
        count_query,
        tuple(params)
    )

    total = total_result[0]["total"] if total_result else 0

    return {
        "logs": rows,
        "total": total,
        "page_size": limit,
        "offset": offset
    }

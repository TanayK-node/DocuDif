import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, PlainTextResponse

from core.config import settings
from services.comparison_service import comparison_service
from services.export_service import generate_csv_report, generate_html_report
import sys

# Ensure ai-engine is in path
ENGINE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ai-engine"
if str(ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(ENGINE_PATH))

from schemas import ComparisonResult, ChangeRecord

router = APIRouter()

@router.get("/health")
def health_check():
    """Health and readiness probe."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "default_provider": settings.DEFAULT_PROVIDER,
        "langgraph_enabled": settings.USE_LANGGRAPH
    }

@router.post("/comparisons", response_model=ComparisonResult)
async def create_comparison(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
    provider: Optional[str] = Form(None),
    threshold: Optional[float] = Form(None),
    use_langgraph: Optional[bool] = Form(True),
    gemini_api_key: Optional[str] = Form(None)
):
    """
    Upload two versions of a document (PDF, DOCX, TXT) and run the comparison engine.
    """
    if gemini_api_key and gemini_api_key.strip():
        os.environ["GEMINI_API_KEY"] = gemini_api_key.strip()
    old_ext = Path(old_file.filename).suffix.lower()
    new_ext = Path(new_file.filename).suffix.lower()

    if old_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format for old_file: {old_ext}")
    if new_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format for new_file: {new_ext}")

    # Unique temporary paths
    job_uuid = str(uuid.uuid4())[:8]
    job_dir = settings.UPLOAD_DIR / job_uuid
    job_dir.mkdir(parents=True, exist_ok=True)

    old_target = job_dir / old_file.filename
    new_target = job_dir / new_file.filename

    try:
        with open(old_target, "wb") as f:
            shutil.copyfileobj(old_file.file, f)
        with open(new_target, "wb") as f:
            shutil.copyfileobj(new_file.file, f)

        # Check file sizes
        if old_target.stat().st_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail="old_file exceeds maximum size limit (25MB).")
        if new_target.stat().st_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail="new_file exceeds maximum size limit (25MB).")

        result = comparison_service.run_comparison(
            old_file_path=old_target,
            new_file_path=new_target,
            provider=provider,
            threshold=threshold,
            use_langgraph=use_langgraph
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison execution failed: {str(e)}")
    finally:
        # Clean up uploaded files after processing
        try:
            shutil.rmtree(job_dir, ignore_errors=True)
        except Exception:
            pass

@router.get("/comparisons")
def list_comparisons():
    """List recent comparison summaries."""
    return comparison_service.list_comparisons()

@router.get("/comparisons/{comparison_id}", response_model=ComparisonResult)
def get_comparison(comparison_id: str):
    """Retrieve full comparison results by ID."""
    result = comparison_service.get_comparison(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Comparison '{comparison_id}' not found.")
    return result

@router.get("/comparisons/{comparison_id}/changes", response_model=List[ChangeRecord])
def get_changes(
    comparison_id: str,
    change_type: Optional[str] = Query(None, description="added, removed, modified, unchanged"),
    priority: Optional[str] = Query(None, description="low, medium, high, critical"),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_unchanged: bool = Query(False)
):
    """Query and filter changes for a comparison."""
    if not comparison_service.get_comparison(comparison_id):
        raise HTTPException(status_code=404, detail=f"Comparison '{comparison_id}' not found.")
    return comparison_service.filter_changes(
        comparison_id=comparison_id,
        change_type=change_type,
        priority=priority,
        category=category,
        search_query=search,
        include_unchanged=include_unchanged
    )

@router.get("/comparisons/{comparison_id}/export")
def export_comparison(
    comparison_id: str,
    format: str = Query("csv", pattern="^(csv|html)$")
):
    """Export comparison report as CSV or standalone HTML."""
    result = comparison_service.get_comparison(comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Comparison '{comparison_id}' not found.")

    if format == "csv":
        csv_data = generate_csv_report(result)
        filename = f"DocuDiff_{comparison_id}_{result.summary.old_filename}_vs_{result.summary.new_filename}.csv"
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )
    elif format == "html":
        html_data = generate_html_report(result)
        filename = f"DocuDiff_{comparison_id}_Report.html"
        return HTMLResponse(
            content=html_data,
            headers={"Content-Disposition": f"inline; filename=\"{filename}\""}
        )

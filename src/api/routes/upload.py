"""
Upload endpoint for PDF files.

TODO: Implement file upload handling
"""

from fastapi import APIRouter, UploadFile, File, BackgroundTasks

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/")
async def upload_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload a PDF file for processing.

    TODO: Implement upload logic
    - Save file
    - Queue processing job
    - Return job ID
    """
    return {"message": "Upload endpoint not yet implemented"}

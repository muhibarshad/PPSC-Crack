"""
Admin Scan Upload Endpoint
============================
POST /api/v1/admin/papers/upload-scan

Accepts up to 4 image uploads (question pages + answer key pages),
stores them in S3/R2, runs GPT-4o Vision OCR, persists questions,
and dispatches the AI pipeline for high-confidence questions.
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.config import settings
from app.dependencies import DBSession, OpenAI, require_admin
from app.models.user import User
from app.schemas.scan_upload import (
    ScanUploadResponse,
    ScanImageInfo,
    OCRStats,
    ReviewStats,
)
from app.services.storage import get_storage_service
from app.services.paper_ingestion.scan_pipeline import run_scan_sync_steps
from app.tasks.paper_ingestion import run_ai_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ────────────────────────────────────────────────
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff"}
MAX_FILE_SIZE = settings.SCAN_MAX_FILE_SIZE_MB * 1024 * 1024  # bytes
MAX_IMAGES = settings.OCR_MAX_IMAGES


@router.post(
    "/papers/upload-scan",
    response_model=ScanUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload scanned paper images for OCR ingestion",
    description=(
        "Accept up to 4 image uploads (questions front/back, answers front/back). "
        "Images are stored in S3/R2, then GPT-4o Vision extracts MCQs and answers. "
        "Questions with OCR confidence < 0.85 go to the Review Queue. "
        "High-confidence questions proceed to the AI pipeline (classify, embed, etc.)."
    ),
)
async def upload_scan(
    db: DBSession,
    openai: OpenAI,
    # ── Form fields ────────────────
    job_type_id: Annotated[str, Form(description="UUID of the target job type")],
    paper_year: Annotated[int, Form(ge=1990, le=2100, description="Paper year")],
    title: Annotated[str, Form(min_length=3, max_length=500, description="Paper title")],
    paper_month: Annotated[int | None, Form(ge=1, le=12, description="Month (optional)")] = None,
    # ── Image uploads ─────────────
    questions_front: UploadFile | None = File(None, description="Questions page (front)"),
    questions_back: UploadFile | None = File(None, description="Questions page (back)"),
    answers_front: UploadFile | None = File(None, description="Answer key (front)"),
    answers_back: UploadFile | None = File(None, description="Answer key (back)"),
    # ── Auth ───────────────────────
    admin: User = Depends(require_admin),
):
    """Upload scanned paper images and run the OCR + ingestion pipeline."""

    # ── Collect uploaded files ────────────────────────────────
    file_map: list[tuple[UploadFile, str]] = []
    for upload, label in [
        (questions_front, "questions_front"),
        (questions_back, "questions_back"),
        (answers_front, "answers_front"),
        (answers_back, "answers_back"),
    ]:
        if upload and upload.filename:
            file_map.append((upload, label))

    if not file_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image file is required.",
        )

    if len(file_map) > MAX_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_IMAGES} images allowed.",
        )

    # ── Validate files ────────────────────────────────────────
    paper_id = uuid.uuid4()
    jtype_id = uuid.UUID(job_type_id)

    files_data: list[tuple[bytes, str, str, int]] = []  # (data, filename, label, size)

    for upload, label in file_map:
        # Check content type
        ct = upload.content_type or ""
        if ct not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{upload.filename}' has unsupported type '{ct}'. "
                       f"Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
            )

        # Read and check size
        data = await upload.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{upload.filename}' exceeds {settings.SCAN_MAX_FILE_SIZE_MB}MB limit.",
            )

        if len(data) < 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{upload.filename}' is too small ({len(data)} bytes). "
                       "Please upload a valid scan image.",
            )

        files_data.append((data, upload.filename or f"{label}.jpg", label, len(data)))

    # ── Upload to S3/R2 ──────────────────────────────────────
    storage = get_storage_service()
    image_urls: list[str] = []
    image_labels: list[str] = []
    image_infos: list[ScanImageInfo] = []

    try:
        for data, filename, label, size in files_data:
            url = await storage.upload_scan_image(
                data, filename, paper_id=paper_id,
            )
            image_urls.append(url)
            image_labels.append(label)
            image_infos.append(ScanImageInfo(
                label=label,
                url=url,
                size_bytes=size,
            ))
    except Exception as exc:
        logger.exception("Failed to upload scan images: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload images: {exc}",
        )

    logger.info(
        "Uploaded %d scan images for paper %s by admin=%s",
        len(image_urls), paper_id, admin.id,
    )

    # ── Run OCR + persist (sync steps) ────────────────────────
    try:
        sync_summary = await run_scan_sync_steps(
            db,
            openai,
            paper_id=paper_id,
            job_type_id=jtype_id,
            paper_year=paper_year,
            paper_month=paper_month,
            title=title,
            image_urls=image_urls,
            image_labels=image_labels,
        )
    except ValueError as exc:
        logger.error("OCR failed for paper %s: %s", paper_id, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"OCR extraction failed: {exc}",
        )
    except Exception as exc:
        logger.exception("Scan ingestion failed for paper %s: %s", paper_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan processing failed: {exc}",
        )

    # ── Dispatch AI pipeline (steps 4-8) for background ──────
    task = run_ai_pipeline.delay(
        paper_id=str(paper_id),
        job_type_id=job_type_id,
        paper_year=paper_year,
    )

    logger.info(
        "Paper %s scan ingestion started. Task=%s. "
        "%d questions, %d need review.",
        paper_id, task.id,
        sync_summary["review_stats"]["total_questions"],
        sync_summary["review_stats"]["needs_review"],
    )

    # ── Build response ────────────────────────────────────────
    ocr = sync_summary.get("ocr_stats", {})
    review = sync_summary.get("review_stats", {})

    return ScanUploadResponse(
        paper_id=paper_id,
        ingestion_status="processing",
        task_id=task.id,
        images=image_infos,
        ocr_stats=OCRStats(
            questions_extracted=ocr.get("questions_extracted", 0),
            answers_extracted=ocr.get("answers_extracted", 0),
            answers_mapped=ocr.get("answers_mapped", 0),
            unmapped_questions=ocr.get("unmapped_questions", []),
        ),
        review_stats=ReviewStats(
            total_questions=review.get("total_questions", 0),
            needs_review=review.get("needs_review", 0),
            auto_approved=review.get("auto_approved", 0),
            confidence_threshold=review.get("confidence_threshold", 0.85),
        ),
        warnings=sync_summary.get("warnings", []),
        sync_processing_time_ms=sync_summary.get("sync_processing_time_ms", 0),
        message=(
            f"Scan processed: {ocr.get('questions_extracted', 0)} questions extracted, "
            f"{review.get('needs_review', 0)} need manual review. "
            "AI pipeline started in background."
        ),
    )

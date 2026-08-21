"""Candidate profile routes."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.db import get_db
from orchestrator.file_validation import (
    MAX_RESUME_SIZE_BYTES,
    sanitize_filename,
    validate_file_content,
)

logger = logging.getLogger(__name__)


class CreateCandidateRequest(BaseModel):
    """Request model for creating a candidate profile"""

    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=1, max_length=255)
    resume_text: str | None = None
    skills: list[str] | None = None


class BulkCandidateItem(BaseModel):
    """A single candidate row within a bulk import request."""

    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=1, max_length=255)
    position: str | None = None
    phone: str | None = None


class BulkCandidateRequest(BaseModel):
    """Request model for bulk candidate import"""

    candidates: list[BulkCandidateItem] = Field(min_length=1)


def create_candidate_routes(candidate_manager) -> APIRouter:
    """Create candidate profile routes."""

    router = APIRouter()

    @router.get("/candidates")
    async def list_candidates(
        limit: int = 100,
        session_db: Session = Depends(get_db),
    ):
        """List all candidates"""
        try:
            candidates = candidate_manager.list_candidates(limit=limit)
            return {"count": len(candidates), "candidates": candidates}
        except Exception as e:
            logger.error(f"Error listing candidates: {e!s}")
            raise HTTPException(status_code=500, detail="Error listing candidates")

    @router.post("/candidates")
    async def create_candidate(
        request: CreateCandidateRequest,
        session_db: Session = Depends(get_db),
    ):
        """Create a new candidate profile"""
        try:
            candidate = candidate_manager.create_candidate(
                name=request.name,
                email=request.email,
                resume_text=request.resume_text,
                skills=request.skills,
            )
            return candidate
        except Exception as e:
            logger.error(f"Error creating candidate: {e!s}")
            raise HTTPException(status_code=500, detail="Error creating candidate")

    @router.post("/candidates/bulk")
    async def bulk_create_candidates(
        request: BulkCandidateRequest,
        session_db: Session = Depends(get_db),
    ):
        """Bulk-create candidate profiles from a CSV import."""
        created = []
        errors = []

        for index, item in enumerate(request.candidates):
            try:
                candidate = candidate_manager.create_candidate(
                    name=item.name,
                    email=item.email,
                )
                candidate["position"] = item.position
                candidate["phone"] = item.phone
                created.append(candidate)
            except Exception as e:
                logger.error(f"Error creating candidate at row {index}: {e!s}")
                errors.append(
                    {
                        "index": index,
                        "email": item.email,
                        "error": str(e),
                    }
                )

        return {
            "imported": len(created),
            "failed": len(errors),
            "candidates": created,
            "errors": errors,
        }

    @router.get("/candidates/{candidate_id}")
    async def get_candidate(
        candidate_id: str,
        session_db: Session = Depends(get_db),
    ):
        """Get candidate details by ID"""
        try:
            candidate = candidate_manager.get_candidate(candidate_id)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
            return candidate
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching candidate: {e!s}")
            raise HTTPException(status_code=500, detail="Error fetching candidate")

    @router.get("/candidates/{candidate_id}/history")
    async def get_candidate_history(
        candidate_id: str,
        session_db: Session = Depends(get_db),
    ):
        """Get candidate interview history"""
        try:
            candidate = candidate_manager.get_candidate(candidate_id)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")
            history = candidate_manager.get_interview_history(candidate_id)
            return {"candidate_id": candidate_id, "history": history}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching candidate history: {e!s}")
            raise HTTPException(
                status_code=500, detail="Error fetching candidate history"
            )

    @router.post("/candidates/{candidate_id}/resume")
    async def upload_candidate_resume(
        candidate_id: str,
        file: UploadFile = File(...),
        session_db: Session = Depends(get_db),
    ):
        """Upload, validate, and save candidate resume."""
        try:
            candidate = candidate_manager.get_candidate(candidate_id)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidate not found")

            content = await file.read()

            # 1. Size check
            if len(content) > MAX_RESUME_SIZE_BYTES:
                raise HTTPException(status_code=413, detail="File too large")

            # 2. Content & Extension validation
            is_valid, err_msg = validate_file_content(
                content, file.filename, file.content_type
            )
            if not is_valid:
                raise HTTPException(status_code=400, detail=err_msg)

            # 3. Sanitize filename
            sanitized_name = sanitize_filename(file.filename)

            # 4. Save resume via manager
            save_method = getattr(candidate_manager, "save_candidate_resume", None)
            if callable(save_method):
                result = save_method(candidate_id, sanitized_name, content)
            else:
                result = {
                    "candidate_id": candidate_id,
                    "filename": sanitized_name,
                    "size_bytes": len(content),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }

            return {"status": "success", "data": result}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading resume: {e!s}")
            raise HTTPException(status_code=500, detail="Error uploading resume")

    return router

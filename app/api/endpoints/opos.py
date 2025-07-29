import logging
from datetime import datetime
from pathlib import Path
from typing import Union
from urllib.parse import urlparse
from app.utils.utils import load_config
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, Field, field_validator
from app.services.analysis_service import run_analysis

router = APIRouter()

# Load BaseLine Instruction Prompt and inject datetime if {$datetime_now$} is present
INSTRUCTION_PROMPT = load_config("app/prompts/instruction.yaml")["prompt"]
INSTRUCTION_PROMPT = INSTRUCTION_PROMPT.replace(
    "{$datetime_now$}", datetime.now().strftime("%dth of %B %Y")
)


class AnalysisRequest(BaseModel):
    """Request model for the analysis endpoint."""

    instruction: str = Field(
        INSTRUCTION_PROMPT, description="The instruction for the analysis"
    )
    workbook_source: str = Field(
        "https://storage.googleapis.com/kritis-documents/Opos-test.xlsx",
        description="The URL or local file path of the workbook to analyze",
    )

    @field_validator("workbook_source")
    @classmethod
    def validate_workbook_source(cls, v: str) -> str:
        """Validate that the workbook source is either a valid URL or an existing local file path."""
        if not v:
            raise ValueError("Workbook source cannot be empty")

        # Check if it's a URL
        parsed = urlparse(v)
        if parsed.scheme in ("http", "https"):
            return v

        # Check if it's a local file path
        file_path = Path(v)
        if file_path.exists() and file_path.is_file():
            # Check if it's an Excel file
            if file_path.suffix.lower() not in [".xlsx", ".xls"]:
                raise ValueError("Local file must be an Excel file (.xlsx or .xls)")
            return str(file_path.resolve())

        raise ValueError(
            "Workbook source must be either a valid URL (http/https) or an existing local Excel file path"
        )

    @property
    def is_url(self) -> bool:
        """Check if the workbook source is a URL."""
        parsed = urlparse(self.workbook_source)
        return parsed.scheme in ("http", "https")

    @property
    def is_local_file(self) -> bool:
        """Check if the workbook source is a local file."""
        return not self.is_url


class AnalysisResponse(BaseModel):
    """Response model for the analysis endpoint."""

    analysis_file_url: str


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_workbook(request: AnalysisRequest):
    """
    Triggers the analysis of a workbook from a given URL or local file path.

    This endpoint initiates the analysis process, which includes:
    1. Loading the workbook from the provided URL or local file path
    2. Processing the data in a secure sandbox environment
    3. Generating an analysis report in a new Excel file
    4. In non-local environments, uploading the result to Google Cloud Storage

    All file operations are performed in a secure temporary directory to prevent
    unauthorized file system access.

    Args:
        request: The analysis request containing the workbook source (URL or local file path).

    Returns:
        A response containing the URL to the analysis file. In local environments,
        this will be a success message with the local file path. In non-local
        environments, this will be a public URL to the file in Google Cloud Storage.

    Raises:
        HTTPException: If an error occurs during the analysis process.
    """
    try:
        result_url = run_analysis(
            instruction=request.instruction,
            workbook_source=request.workbook_source,
            is_local_file=request.is_local_file,
        )
        return {"analysis_file_url": result_url}

    except HTTPException as he:
        raise he

    except Exception as e:
        logging.exception("Error during analysis")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )

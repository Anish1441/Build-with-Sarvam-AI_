from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ThreeLineCard(BaseModel):
    when: str = Field(..., description="Hearing date and time, e.g. '14 नोव्हेंबर 2024, सकाळी 11:00'")
    where: str = Field(..., description="Court name and room, e.g. 'दिवाणी न्यायालय कनिष्ठ स्तर, हवेली पुणे'")
    what_to_bring: List[str] = Field(default_factory=list, description="List of physical documents needed, e.g. ['७/१२ उतारा', 'खरेदी खत मूळ प्रत']")

class OrderSheetExtraction(BaseModel):
    case_number: str = Field(..., description="Case number or CNR, e.g. 'RCS 142/2024'")
    court_name: str = Field(..., description="Full court designation")
    hearing_date: str = Field(..., description="Date of the current hearing (DD/MM/YYYY)")
    next_date: str = Field(..., description="Next date fixed for hearing (DD/MM/YYYY)")
    stage: str = Field(..., description="Legal stage, e.g. 'Evidence', 'Arguments', 'Written Statement', 'Steps'")
    order_summary: str = Field(..., description="Summary of what the judge actually ordered")
    action_required: str = Field(..., description="Who must do what before the next date")
    documents_needed: List[str] = Field(default_factory=list, description="Documents required to be submitted")
    confidence_score: float = Field(0.95, ge=0.0, le=1.0, description="Extraction confidence score")
    three_line_card: Optional[ThreeLineCard] = None

class LawyerClaim(BaseModel):
    transcript: str = Field(..., description="Raw transcript of the lawyer's voice note from Saaras STT")
    claimed_stage: str = Field(..., description="Stage of case claimed by lawyer, e.g. 'Evidence recorded'")
    claimed_next_date: Optional[str] = Field(None, description="Next date claimed by lawyer")
    claimed_action: str = Field(..., description="What lawyer claimed was done or needs to be done")
    confidence_score: float = Field(0.90, ge=0.0, le=1.0)

class MismatchAnalysis(BaseModel):
    has_mismatch: bool = Field(..., description="True if a discrepancy is detected between lawyer claim and court order")
    severity: str = Field("GENTLE", description="GENTLE, MODERATE, or CRITICAL")
    court_verbatim: str = Field(..., description="What the court order actually states")
    lawyer_verbatim: str = Field(..., description="What the lawyer claimed in the voice update")
    mismatch_summary_en: str = Field(..., description="Objective explanation in English")
    mismatch_summary_mr: str = Field(..., description="Gentle, non-accusatory Marathi explanation for the farmer")
    suggested_questions_mr: List[str] = Field(default_factory=list, description="Gentle, polite questions to ask the lawyer in Marathi")
    suggested_questions_en: List[str] = Field(default_factory=list, description="Suggested questions in English")

class VoiceDiaryEntry(BaseModel):
    id: Optional[int] = None
    case_number: str
    date: str
    title_en: str
    title_mr: str
    summary_mr: str
    audio_path: Optional[str] = None
    has_mismatch: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

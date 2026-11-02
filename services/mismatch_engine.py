import json
import re
from typing import Dict, Any
from services.sarvam_client import get_sarvam_client
from config import CHAT_MODEL
from models import LawyerClaim, OrderSheetExtraction, MismatchAnalysis
from services.explainer_service import clean_json_response

def extract_lawyer_claims(transcript: str) -> LawyerClaim:
    """
    Extracts structured claims from the transcribed voice note of the lawyer.
    """
    client = get_sarvam_client()
    
    prompt = f"""You are analyzing a transcript of a voice update given by an Indian advocate to a rural client.
Extract what the lawyer claims occurred in the hearing and what next steps were communicated.

Transcript:
"{transcript}"

Extract strictly the following JSON structure:
{{
  "claimed_stage": "What the lawyer said happened (e.g., Evidence completed, Arguments heard, Notice issued, Adjournment taken)",
  "claimed_next_date": "Next date mentioned by lawyer, or null if unmentioned",
  "claimed_action": "What the lawyer claimed was done or what the litigant needs to do",
  "confidence_score": 0.92
}}

Return ONLY JSON.
"""
    response = client.chat.completions(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    raw = response.choices[0].message.content or "{}"
    cleaned = clean_json_response(raw)
    data = json.loads(cleaned)
    data["transcript"] = transcript
    return LawyerClaim(**data)

def compare_lawyer_vs_order(lawyer_claim: LawyerClaim, order_sheet: OrderSheetExtraction) -> MismatchAnalysis:
    """
    The Hero Feature: Compares what the lawyer claimed against what the court order actually states.
    CRITICAL GUARDRAIL: Framing must NEVER accuse or malign the lawyer.
    It empowers the litigant to ask informed, respectful, and clarifying questions.
    """
    client = get_sarvam_client()
    
    prompt = f"""You are the mismatch analyzer for 'Tareekh', an assistive legal transparency tool for rural Indian litigants.
Compare the lawyer's verbal claims against the official written court order sheet.

Official Written Court Order:
- Case: {order_sheet.case_number}
- Court: {order_sheet.court_name}
- Hearing Date: {order_sheet.hearing_date}
- Actual Stage/Order: {order_sheet.stage} - {order_sheet.order_summary}
- Actual Next Date: {order_sheet.next_date}
- Required Documents: {', '.join(order_sheet.documents_needed) if order_sheet.documents_needed else 'None'}

Lawyer's Verbal Claims (Transcribed from Voice Note):
- What Lawyer Claimed: {lawyer_claim.claimed_stage}
- Claimed Next Date: {lawyer_claim.claimed_next_date or 'Not stated'}
- Claimed Action: {lawyer_claim.claimed_action}

Guidelines:
1. Detect whether there is a meaningful discrepancy (e.g., lawyer claimed 'evidence was recorded/complete', but court order says 'adjourned for filing documents/evidence not taken').
2. Severity must be: 'GENTLE', 'MODERATE', or 'CRITICAL'.
3. The tone MUST be respectful, constructive, and neutral. Never accuse the lawyer of lying or negligence.
4. Provide 'mismatch_summary_mr' in clear, polite Marathi suitable for a Marathi-speaking farmer.
5. Provide 2-3 polite, empowering questions ('suggested_questions_mr') in Marathi that the client can ask their advocate to get clarification.
6. Provide English versions for the family member dashboard.

Extract strictly the following JSON structure:
{{
  "has_mismatch": true,
  "severity": "MODERATE",
  "court_verbatim": "Brief summary of court order",
  "lawyer_verbatim": "Brief summary of lawyer statement",
  "mismatch_summary_en": "Objective English explanation",
  "mismatch_summary_mr": "Marathi gentle explanation",
  "suggested_questions_mr": [
    "वकील साहेबांना विचारण्यासाठी प्रश्न १...",
    "वकील साहेबांना विचारण्यासाठी प्रश्न २..."
  ],
  "suggested_questions_en": [
    "Question 1 in English...",
    "Question 2 in English..."
  ]
}}

Return ONLY valid JSON.
"""
    response = client.chat.completions(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    
    raw = response.choices[0].message.content or "{}"
    cleaned = clean_json_response(raw)
    
    try:
        data = json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise ValueError(f"Failed to parse mismatch analysis JSON: {raw}")
            
    return MismatchAnalysis(**data)

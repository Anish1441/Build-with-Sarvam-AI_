import os
import json
from config import BASE_DIR
from models import OrderSheetExtraction, LawyerClaim
from services.explainer_service import parse_order_sheet_text, explain_legal_term
from services.speech_service import synthesize_speech, transcribe_audio
from services.mismatch_engine import extract_lawyer_claims, compare_lawyer_vs_order
import db

def run_test():
    print("=== STEP 1: INITIALIZING DATABASE ===")
    db.init_db()
    case_num = "RCS 142/2024"
    db.save_case(
        case_number=case_num,
        litigant_name="Tukaram Babanrao Patil (तुकाराम बाबनराव पाटील)",
        court_name="Civil Court Junior Division, Haveli Pune",
        language="mr-IN",
        relative_name="Sagar Patil (Son - Pune)",
        relative_contact="+91 98220 12345"
    )
    print(f"Case {case_num} registered successfully.")

    print("\n=== STEP 2: PARSING REALISTIC COURT ORDER SHEET (SARVAM-105B) ===")
    mock_order_text = """
    IN THE COURT OF CIVIL JUDGE JUNIOR DIVISION, HAVELI, PUNE
    REGULAR CIVIL SUIT NO. 142 OF 2024
    Tukaram Babanrao Patil ... Plaintiff
    V/S
    Sopan Vitthal Shinde ... Defendant
    
    ORDER BELOW EXH. 1
    Date: 28/10/2024
    Advocate for Plaintiff present. Advocate for Defendant present.
    Plaintiff's counsel sought time to file certified copy of 7/12 extract and original registered sale deed of Gat No. 45/2.
    No evidence recorded today. Adjourned at plaintiff's request.
    Next date fixed on 14/11/2024 for filing documents and steps.
    Sd/- CJJD Haveli
    """
    
    order_data = parse_order_sheet_text(mock_order_text)
    print(f"Extracted Case: {order_data.case_number}")
    print(f"Next Date: {order_data.next_date}")
    print(f"Stage: {order_data.stage}")
    print(f"Action Required: {order_data.action_required}")
    print(f"Documents Needed: {order_data.documents_needed}")
    print(f"Three-Line Card (When): {order_data.three_line_card.when}")
    print(f"Three-Line Card (What to bring): {order_data.three_line_card.what_to_bring}")

    print("\n=== STEP 3: SYNTHESIZING MARATHI SPOKEN SUMMARY (BULBUL:V3) ===")
    spoken_script_mr = (
        f"पाटील काका, तुमच्या जमिनीच्या केसमध्ये पुढील तारीख {order_data.next_date} आहे. "
        f"न्यायालयाने मूळ खरेदी खत आणि सात बारा उतारा मागितला आहे. सोबत घेऊन जाणे गरजेचे आहे."
    )
    audio_path, _ = synthesize_speech(
        text=spoken_script_mr,
        language_code="mr-IN",
        speaker="rohan",
        filename_prefix="hearing_reminder"
    )
    print(f"Bulbul TTS audio generated at: {audio_path}")

    print("\n=== STEP 4: TRANSCRIBING LAWYER VOICE NOTE WITH SAARAS:V3 ===")
    # First synthesize the lawyer's Hinglish/Marathi voice note to simulate audio file
    lawyer_spoken = "पाटील साहेब, काळजी करू नका. आज कोर्टात आपलं एविडन्स पूर्ण झालं आहे. पुढची तारीख साहेबांनी ऑर्डरसाठी ठेवली आहे."
    simulated_voice_note_path, _ = synthesize_speech(
        text=lawyer_spoken,
        language_code="mr-IN",
        speaker="aditya",
        filename_prefix="lawyer_voice_note"
    )
    
    # Transcribe with Saaras STT
    transcript = transcribe_audio(simulated_voice_note_path, language_code="mr-IN", mode="codemix")
    print(f"Saaras STT Transcribed Text: {transcript}")

    print("\n=== STEP 5: HERO FEATURE - LAWYER VS COURT MISMATCH ANALYSIS ===")
    lawyer_claims = extract_lawyer_claims(transcript)
    print(f"Lawyer Claims: Stage='{lawyer_claims.claimed_stage}', Action='{lawyer_claims.claimed_action}'")
    
    mismatch = compare_lawyer_vs_order(lawyer_claims, order_data)
    print(f"Mismatch Detected: {mismatch.has_mismatch} (Severity: {mismatch.severity})")
    print(f"Court Verbatim: {mismatch.court_verbatim}")
    print(f"Lawyer Verbatim: {mismatch.lawyer_verbatim}")
    print(f"English Summary: {mismatch.mismatch_summary_en}")
    print(f"Marathi Gentle Summary: {mismatch.mismatch_summary_mr}")
    print("\nSuggested Polite Questions for the Lawyer (Marathi):")
    for q in mismatch.suggested_questions_mr:
        print(f"  - {q}")

    print("\n=== STEP 6: PERSISTING TO DB & VOICE CASE DIARY ===")
    sheet_id = db.save_order_sheet(
        case_number=order_data.case_number,
        hearing_date=order_data.hearing_date,
        next_date=order_data.next_date,
        stage=order_data.stage,
        order_summary=order_data.order_summary,
        action_required=order_data.action_required,
        documents=order_data.documents_needed,
        confidence=order_data.confidence_score,
        raw_text=mock_order_text,
        audio_path=audio_path
    )
    
    note_id = db.save_lawyer_note(
        case_number=order_data.case_number,
        audio_path=simulated_voice_note_path,
        transcript=transcript,
        claimed_stage=lawyer_claims.claimed_stage,
        claimed_action=lawyer_claims.claimed_action,
        claimed_next_date=lawyer_claims.claimed_next_date or ""
    )
    
    m_id = db.save_mismatch(
        case_number=order_data.case_number,
        hearing_date=order_data.hearing_date,
        has_mismatch=mismatch.has_mismatch,
        severity=mismatch.severity,
        summary_en=mismatch.mismatch_summary_en,
        summary_mr=mismatch.mismatch_summary_mr,
        court_claim=mismatch.court_verbatim,
        lawyer_claim=mismatch.lawyer_verbatim,
        questions=mismatch.suggested_questions_mr
    )
    
    db.save_diary_entry(
        case_number=order_data.case_number,
        entry_date=order_data.hearing_date,
        title_en="Hearing: Documents Adjournment & Discrepancy Noted",
        title_mr="सुनावणी: कागदपत्रांसाठी तारीख पुढे ढकलली",
        summary_mr=mismatch.mismatch_summary_mr,
        audio_path=audio_path,
        has_mismatch=mismatch.has_mismatch
    )
    
    diary = db.get_diary(case_num)
    print(f"Case diary now has {len(diary)} entries.")
    print("=== PHASE 1 TEST COMPLETED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_test()

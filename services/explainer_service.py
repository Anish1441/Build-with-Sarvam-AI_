import json
import re
from typing import Dict, Any, List
from services.sarvam_client import get_sarvam_client
from config import CHAT_MODEL, TRANSLATE_MODEL, DEFAULT_LANGUAGE
from models import OrderSheetExtraction, ThreeLineCard

def translate_text(text: str, source_lang: str = "en-IN", target_lang: str = "mr-IN") -> str:
    """Translates text using Sarvam Mayura:v1"""
    client = get_sarvam_client()
    res = client.text.translate(
        input=text,
        source_language_code=source_lang,
        target_language_code=target_lang,
        model=TRANSLATE_MODEL
    )
    return res.translated_text or text

def clean_json_response(content: str) -> str:
    """Strips markdown code fences and returns pure JSON string."""
    cleaned = content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def parse_order_sheet_text(raw_order_text: str) -> OrderSheetExtraction:
    """
    Uses Sarvam-105B to convert raw court order sheet text/shorthand into structured JSON.
    """
    client = get_sarvam_client()
    
    prompt = f"""You are a specialized legal document extraction assistant for Indian district and taluka court order sheets.
Analyze the following court order sheet and extract the fields accurately in JSON format.

Order Sheet Text:
{raw_order_text}

Extract strictly the following JSON structure:
{{
  "case_number": "CNR or Case Number, e.g. RCS 142/2024",
  "court_name": "Full Court Name and Location",
  "hearing_date": "DD/MM/YYYY of the hearing recorded on this sheet",
  "next_date": "DD/MM/YYYY of the next fixed hearing date",
  "stage": "Procedural stage (e.g. Evidence, Arguments, Written Statement, Steps, Notice)",
  "order_summary": "Precise summary in plain English of what the Judge actually directed/ordered",
  "action_required": "Who must do what before or on the next date",
  "documents_needed": ["List of physical documents requested by the court"],
  "confidence_score": 0.95
}}

Return ONLY valid JSON. Do not add markdown explanation or extra conversational commentary.
"""
    response = client.chat.completions(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    raw_content = response.choices[0].message.content or "{}"
    cleaned = clean_json_response(raw_content)
    
    try:
        data = json.loads(cleaned)
    except Exception:
        # Fallback regex extraction if model included any prefix
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise ValueError(f"Failed to parse JSON from Sarvam-105B response: {raw_content}")
            
    # Generate Marathi 3-line card
    three_line_card = generate_three_line_card(data)
    data["three_line_card"] = three_line_card.model_dump()
    
    return OrderSheetExtraction(**data)

def generate_three_line_card(extracted_data: Dict[str, Any]) -> ThreeLineCard:
    """
    Produces the clear, minimal 3-line card in Marathi:
    1. When (केव्हा)
    2. Where (कुठे)
    3. What to bring (काय सोबत आणायचे)
    """
    next_date = extracted_data.get("next_date", "तारीख नमूद नाही")
    court_name = extracted_data.get("court_name", "न्यायालय")
    docs = extracted_data.get("documents_needed", [])
    
    # Translate and format into simple Marathi
    when_mr = f"{next_date}, सकाळी १०:३० वाजता"
    where_mr = court_name
    
    # Convert docs to Marathi if needed
    docs_mr = []
    if docs:
        for doc in docs:
            translated = translate_text(doc, source_lang="en-IN", target_lang="mr-IN")
            docs_mr.append(translated)
    else:
        docs_mr = ["कोणतेही अतिरिक्त कागदपत्र आवश्यक नाही (फक्त स्वतः हजर राहणे)"]
        
    return ThreeLineCard(
        when=when_mr,
        where=where_mr,
        what_to_bring=docs_mr
    )

def explain_legal_term(term: str, language: str = "mr-IN") -> str:
    """
    On-demand glossary: converts complex legal terms (e.g. 'adjournment', 'ex-parte', 'vakalatnama')
    into intuitive, compassionate explanation for a rural litigant.
    """
    client = get_sarvam_client()
    prompt = f"""Explain the legal concept '{term}' in very simple, easy-to-understand Marathi for a farmer litigant.
Explain:
1. What it means in everyday words (no legal jargon).
2. What it means for their case (does it hurt them or help them?).
3. What they should ask their lawyer about it.

Keep it under 3 short sentences. Be compassionate and clear.
"""
    response = client.chat.completions(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content or ""

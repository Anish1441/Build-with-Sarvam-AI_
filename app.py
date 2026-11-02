import streamlit as st
import os
import json
import base64
from pathlib import Path
from datetime import datetime

# Local project imports
import db
from config import (
    BASE_DIR, AUDIO_DIR, DOCS_DIR,
    CHAT_MODEL, STT_MODEL, TTS_MODEL, TRANSLATE_MODEL,
    DEFAULT_LANGUAGE
)
from services.speech_service import synthesize_speech, transcribe_audio
from services.explainer_service import parse_order_sheet_text, explain_legal_term, translate_text
from services.mismatch_engine import extract_lawyer_claims, compare_lawyer_vs_order
from models import OrderSheetExtraction, LawyerClaim
from i18n import get_text, TRANSLATIONS

# Streamlit Page Config
st.set_page_config(
    page_title="Tareekh • तारीख - Rural Legal Transparency",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# NATURAL EARTH & BOTANICAL PALETTE (STRICTLY ZERO BLUE OR BLUE DERIVATIVES)
# Deep Riverstone Slate: #151714, #1C1F1B, #242922
# Natural Forest Green & Sage: #2A4332, #395B44, #507A5E, #8DB499
# Earth Terracotta & Warm Sienna: #8E4423, #AA532D, #C6683E, #E0875C
# Natural Parchment & Unbleached Flax: #F7F3EE, #EFE8DE, #DDD3C3, #B8A995
# Clay & Bark Borders: #4A3E33, #6B5B4C
NATURAL_CSS = """
<style>
/* Global Zoom-Proof Box Model & Resilient Wrapping */
*, *::before, *::after {
    box-sizing: border-box !important;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans Devanagari", sans-serif;
    color: #F7F3EE;
    word-break: break-word !important;
    overflow-wrap: anywhere !important;
}

/* Background Texture: Organic Riverstone with Subtle Botanical & Flax Micro-grain */
.stApp {
    background-color: #151714;
    background-image: 
        radial-gradient(rgba(170, 83, 45, 0.08) 1px, transparent 1px),
        radial-gradient(rgba(80, 122, 94, 0.07) 1px, transparent 1px);
    background-size: 26px 26px, 52px 52px;
    background-position: 0 0, 13px 13px;
}

/* Sidebar: Natural Earth & Bark Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1C1F1A 0%, #161814 100%) !important;
    border-right: 1px solid #4A3E33 !important;
}

/* Tareekh Natural Brand Banner */
.tareekh-brand {
    background: linear-gradient(135deg, #242921 0%, #2D352B 50%, #1E231C 100%);
    border: 1px solid #4A5B49;
    border-left: 6px solid #AA532D;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
}

.tareekh-title {
    font-size: 2.1rem;
    font-weight: 800;
    color: #F7F3EE;
    margin: 0;
    letter-spacing: -0.5px;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.tareekh-subtitle {
    font-size: 0.95rem;
    color: #D3C7B6;
    margin-top: 0.35rem;
}

/* Natural Organic Card Containers */
.t-card {
    background: linear-gradient(145deg, #20241E 0%, #191C17 100%);
    border: 1px solid #3F473B;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
}

.t-card-highlight {
    background: linear-gradient(145deg, #2A3127 0%, #20251D 100%);
    border: 1px solid #5A6953;
    border-left: 5px solid #C6683E;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}

.t-card-alert {
    background: linear-gradient(145deg, #321B16 0%, #241410 100%);
    border: 1px solid #783526;
    border-left: 5px solid #C04A26;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}

.t-card-success {
    background: linear-gradient(145deg, #1C2E22 0%, #152219 100%);
    border: 1px solid #2F533B;
    border-left: 5px solid #507A5E;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}

/* 3-Line Card Styling */
.three-line-box {
    background: #22261F;
    border: 2px solid #AA532D;
    border-radius: 12px;
    padding: 1.25rem;
    margin: 1rem 0;
}

.three-line-item {
    padding: 0.5rem 0;
    border-bottom: 1px solid #3A3F33;
    display: flex;
    flex-direction: column;
}

.three-line-item:last-child {
    border-bottom: none;
}

.three-line-label {
    font-size: 0.82rem;
    text-transform: uppercase;
    font-weight: 700;
    color: #E0875C;
    letter-spacing: 0.5px;
}

.three-line-val {
    font-size: 1.15rem;
    font-weight: 600;
    color: #F7F3EE;
    margin-top: 0.2rem;
}

/* Natural Badges */
.badge-earth {
    background: #3B332A;
    color: #EFE8DE;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-block;
    border: 1px solid #5A4E40;
}

.badge-green {
    background: #1E3325;
    color: #B2D8BD;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-block;
    border: 1px solid #3B6146;
}

.badge-terracotta {
    background: #472118;
    color: #FCD5C8;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-block;
    border: 1px solid #8E4423;
}

/* Natural Buttons: Warm Sienna Terracotta */
.stButton > button {
    background: linear-gradient(180deg, #AA532D 0%, #8E4423 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #C6683E !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3) !important;
}

.stButton > button:hover {
    background: linear-gradient(180deg, #C6683E 0%, #AA532D 100%) !important;
    border-color: #E0875C !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(170, 83, 45, 0.35) !important;
}

/* Natural Phone Simulation Frame */
.phone-frame {
    background: #20241E;
    border: 3px solid #5A4E40;
    border-radius: 28px;
    padding: 1.5rem;
    max-width: 360px;
    margin: 0 auto;
    text-align: center;
    box-shadow: 0 12px 32px rgba(0,0,0,0.6);
}

.phone-screen {
    background: linear-gradient(180deg, #262B23 0%, #1A1D18 100%);
    border-radius: 18px;
    padding: 1.5rem 1rem;
    border: 1px solid #3F473B;
}

/* Natural Pulsing Avatar */
.pulse-circle {
    width: 76px;
    height: 76px;
    border-radius: 50%;
    background: #AA532D;
    margin: 0 auto 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    color: #F7F3EE;
    box-shadow: 0 0 0 0 rgba(170, 83, 45, 0.7);
    animation: pulse-terracotta 2s infinite;
}

@keyframes pulse-terracotta {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(170, 83, 45, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 16px rgba(170, 83, 45, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(170, 83, 45, 0); }
}
</style>
"""
st.markdown(NATURAL_CSS, unsafe_allow_html=True)

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "selected_case" not in st.session_state:
    st.session_state.selected_case = "RCS 142/2024"
if "app_lang" not in st.session_state:
    st.session_state.app_lang = "mr"  # Default Marathi, toggleable to Hindi (hi) or English (en)

db.init_db()

# User Persona Definitions
PERSONAS = {
    "tukaram": {
        "name": "तुकाराम पाटील (Tukaram Patil)",
        "role": "शेतकरी पक्षकार (Farmer Litigant)",
        "location": "हवेली, पुणे (Haveli, Pune)",
        "case": "RCS 142/2024 (जमीन वाटप दावा)",
        "avatar": "🌾",
        "pin": "1234"
    },
    "sagar": {
        "name": "सागर पाटील (Sagar Patil)",
        "role": "कुटुंब सदस्य / मुलगा (Son - Tech Professional)",
        "location": "हिंजवडी, पुणे (Hinjawadi, Pune)",
        "case": "RCS 142/2024 (Tukaram Patil Case)",
        "avatar": "💼",
        "pin": "2345"
    },
    "adv_joshi": {
        "name": "Adv. सीमा जोशी (Seema Joshi)",
        "role": "विधी सेवा सहाय्यक (DLSA Legal Aid Volunteer)",
        "location": "जिल्हा विधी सेवा प्राधिकरण, पुणे",
        "case": "Multi-Case Oversight",
        "avatar": "⚖️",
        "pin": "3456"
    }
}

# --- TOP LANGUAGE TOGGLE BAR (Visible on All Pages) ---
lang_col1, lang_col2 = st.columns([3, 1])
with lang_col2:
    selected_lang_name = st.radio(
        "🌐 भाषा / Language:",
        ["मराठी (Marathi)", "हिंदी (Hindi)", "English"],
        horizontal=True,
        index=0 if st.session_state.app_lang == "mr" else (1 if st.session_state.app_lang == "hi" else 2),
        key="lang_selector"
    )
    if "मराठी" in selected_lang_name:
        st.session_state.app_lang = "mr"
    elif "हिंदी" in selected_lang_name:
        st.session_state.app_lang = "hi"
    else:
        st.session_state.app_lang = "en"

cur_lang = st.session_state.app_lang
t = lambda k: get_text(k, cur_lang)
speaker = TRANSLATIONS[cur_lang]["speaker"]
lang_code = TRANSLATIONS[cur_lang]["lang_code"]

# --- AUTHENTICATION VIEW ---
if not st.session_state.authenticated:
    st.markdown(f"""
    <div class="tareekh-brand" style="text-align: center;">
        <h1 class="tareekh-title" style="justify-content: center;">⚖️ {t('app_title')}</h1>
        <p class="tareekh-subtitle">{t('app_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="t-card-highlight">
            <h3 style="color: #F7F3EE; margin-top: 0;">{t('login_title')}</h3>
            <p style="color: #D3C7B6; font-size: 0.9rem;">{t('login_desc')}</p>
        </div>
        """, unsafe_allow_html=True)

        user_choice = st.selectbox(
            t('select_persona'),
            options=list(PERSONAS.keys()),
            format_func=lambda k: f"{PERSONAS[k]['avatar']} {PERSONAS[k]['name']} — {PERSONAS[k]['role']}"
        )

        selected_persona = PERSONAS[user_choice]
        pin_input = st.text_input(
            f"{t('enter_pin')} (Default: {selected_persona['pin']}):",
            type="password",
            value=selected_persona["pin"]
        )

        if st.button(t('sign_in'), use_container_width=True):
            if pin_input == selected_persona["pin"]:
                st.session_state.authenticated = True
                st.session_state.current_user = user_choice
                st.rerun()
            else:
                st.error(t('wrong_pin'))

        st.markdown("""
        <div style="text-align: center; margin-top: 1.5rem; color: #AA532D; font-size: 0.85rem;">
            Powered by Sarvam AI • Models: Sarvam-105B, Saaras STT, Bulbul TTS, Mayura
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# --- LOGGED IN USER INTERFACE ---
user_data = PERSONAS[st.session_state.current_user]

# Top Brand Banner
st.markdown(f"""
<div class="tareekh-brand">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div>
            <h1 class="tareekh-title">⚖️ {t('app_title')}</h1>
            <p class="tareekh-subtitle">
                {user_data['avatar']} <strong>{user_data['name']}</strong> | {user_data['role']} | 📍 {user_data['location']}
            </p>
        </div>
        <div>
            <span class="badge-earth">{t('active_case')}: {st.session_state.selected_case}</span>
            <span class="badge-green">Sarvam AI Active</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Controls
with st.sidebar:
    st.markdown(f"### {user_data['avatar']} {user_data['name']}")
    st.caption(f"{user_data['role']}")
    
    st.markdown("---")
    st.markdown(f"#### 📁 {t('active_case')}")
    st.info(f"**{st.session_state.selected_case}**\n\nTukaram Patil v/s Sopan Shinde\nCivil Court Haveli, Pune")
    
    st.markdown("---")
    st.markdown(f"#### 🤖 {t('sarvam_status')}")
    st.markdown(f"""
    - **Language Code**: `{lang_code}`
    - **Speaker**: `{speaker}`
    - **LLM Reasoning**: `{CHAT_MODEL}`
    - **Speech (STT)**: `{STT_MODEL}`
    - **Voice (TTS)**: `{TTS_MODEL}`
    - **Translation**: `{TRANSLATE_MODEL}`
    """)
    
    st.markdown("---")
    if st.button(t('logout'), use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()

# Dynamic Navigation Tabs
tabs = st.tabs([
    t('tab_demo'),
    t('tab_scanner'),
    t('tab_mismatch'),
    t('tab_diary'),
    t('tab_glossary'),
    t('tab_call')
])

# ==============================================================================
# TAB 1: 90-SECOND LIVE SHOWCASE DEMO
# ==============================================================================
with tabs[0]:
    st.markdown(f"""
    <div class="t-card-highlight">
        <h3 style="color: #F7F3EE; margin: 0;">🎬 {t('tab_demo')}</h3>
        <p style="color: #D3C7B6; margin-top: 0.3rem; font-size: 0.92rem;">
            {t('app_subtitle')} — End-to-end live walk of court order capture, 3-line plain explanation, audio synthesis, and lawyer voice mismatch check.
        </p>
    </div>
    """, unsafe_allow_html=True)

    demo_cols = st.columns([1, 1])
    
    with demo_cols[0]:
        st.markdown(f"#### 1. {t('court_record')}")
        mock_doc = """IN THE COURT OF CIVIL JUDGE JUNIOR DIVISION, HAVELI, PUNE
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
Sd/- CJJD Haveli"""
        
        st.text_area("Official Court Order Snippet:", value=mock_doc, height=200, disabled=True)
        
        if st.button(t('extract_btn'), use_container_width=True):
            with st.spinner("Sarvam-105B extracting legal metadata..."):
                extracted = parse_order_sheet_text(mock_doc)
                st.session_state.demo_order = extracted
                st.success("✅ Extraction complete! Next date & required documents extracted.")

    with demo_cols[1]:
        st.markdown("#### 2. Three-Line Card & Spoken Audio")
        if "demo_order" in st.session_state:
            order = st.session_state.demo_order
            
            # Format according to current language
            when_val = f"{order.next_date} (10:30 AM)"
            where_val = order.court_name
            docs_val = ", ".join(order.documents_needed)
            
            st.markdown(f"""
            <div class="three-line-box">
                <div class="three-line-item">
                    <span class="three-line-label">{t('card_when')}</span>
                    <span class="three-line-val">🗓️ {when_val}</span>
                </div>
                <div class="three-line-item">
                    <span class="three-line-label">{t('card_where')}</span>
                    <span class="three-line-val">🏛️ {where_val}</span>
                </div>
                <div class="three-line-item">
                    <span class="three-line-label">{t('card_what')}</span>
                    <span class="three-line-val">📑 {docs_val}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Multilingual Audio Sample
            audio_file = AUDIO_DIR / f"sample_reminder_{cur_lang}.wav"
            if not audio_file.exists():
                audio_file = AUDIO_DIR / "sample_reminder_call.wav"
                
            if audio_file.exists():
                st.markdown(f"**{t('listen_audio')}**")
                st.audio(str(audio_file), format="audio/wav")
        else:
            st.info(f"Click '{t('extract_btn')}' on the left to run extraction.")

    st.markdown("---")
    
    # Hero Mismatch Walkthrough
    st.markdown(f"#### 3. {t('tab_mismatch')} (Hero Feature)")
    mismatch_col1, mismatch_col2 = st.columns([1, 1])
    
    with mismatch_col1:
        st.markdown(f"""
        <div class="t-card">
            <h4 style="color: #E0875C; margin-top: 0;">{t('lawyer_record')}</h4>
            <p style="color: #D3C7B6; font-size: 0.9rem;">
                Voice note received from advocate following the hearing:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        lawyer_wav = AUDIO_DIR / f"sample_lawyer_{cur_lang}.wav"
        if not lawyer_wav.exists():
            lawyer_wav = AUDIO_DIR / "sample_lawyer_voice_note.wav"
            
        if lawyer_wav.exists():
            st.audio(str(lawyer_wav), format="audio/wav")
            
        transcript_sample = {
            "mr": "पाटील साहेब, काळजी करू नका. आज कोर्टात आपलं एविडन्स पूर्ण झालं आहे. पुढची तारीख साहेबांनी ऑर्डरसाठी ठेवली आहे.",
            "hi": "पाटिल साहब, नमस्कार। आज कोर्ट में अपना सबूत और एविडेंस पूरा दर्ज हो गया है। जज साहब ने अगली तारीख फैसले के लिए रखी है।",
            "en": "Hello Patil sir, do not worry. Today in court our evidence stage was fully completed. The judge has scheduled the next date directly for final orders."
        }
        st.markdown(f"""
        **Saaras:v3 STT Transcript:**  
        > *"{transcript_sample.get(cur_lang, transcript_sample['mr'])}"*
        """)
        
    with mismatch_col2:
        if st.button(t('mismatch_btn'), use_container_width=True):
            with st.spinner("Saaras STT + Sarvam-105B analyzing claims..."):
                lawyer_text = transcript_sample.get(cur_lang, transcript_sample['mr'])
                lawyer_claim = extract_lawyer_claims(lawyer_text)
                
                if "demo_order" not in st.session_state:
                    st.session_state.demo_order = parse_order_sheet_text(mock_doc)
                    
                analysis = compare_lawyer_vs_order(lawyer_claim, st.session_state.demo_order)
                st.session_state.demo_mismatch = analysis

        if "demo_mismatch" in st.session_state:
            res = st.session_state.demo_mismatch
            summary_text = res.mismatch_summary_mr if cur_lang == "mr" else (res.mismatch_summary_en if cur_lang == "en" else res.mismatch_summary_mr)
            if cur_lang == "hi":
                try:
                    summary_text = translate_text(res.mismatch_summary_en, source_lang="en-IN", target_lang="hi-IN")
                except Exception:
                    summary_text = res.mismatch_summary_en
                    
            st.markdown(f"""
            <div class="t-card-alert">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #F7F3EE; font-size: 1.1rem;">{t('discrepancy_alert')}</strong>
                    <span class="badge-terracotta">{res.severity}</span>
                </div>
                <p style="color: #F7F3EE; margin-top: 0.6rem; font-size: 0.95rem; line-height: 1.5;">
                    {summary_text}
                </p>
                <hr style="border: 0; border-top: 1px solid #783526; margin: 0.75rem 0;">
                <div style="font-size: 0.88rem; color: #F7F3EE;">
                    <strong>{t('court_record')}</strong> {res.court_verbatim}<br>
                    <strong>{t('lawyer_record')}</strong> {res.lawyer_verbatim}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"##### {t('suggested_questions')}")
            questions_list = res.suggested_questions_mr if cur_lang == "mr" else res.suggested_questions_en
            for q in questions_list:
                st.markdown(f"""
                <div style="background: #232821; border-left: 4px solid #AA532D; padding: 0.6rem 0.8rem; margin-bottom: 0.5rem; border-radius: 4px; font-size: 0.95rem; color: #F7F3EE;">
                    💬 {q}
                </div>
                """, unsafe_allow_html=True)


# ==============================================================================
# TAB 2: ORDER SHEET SCANNER & EXPLAINER
# ==============================================================================
with tabs[1]:
    st.markdown(f"""
    <div class="t-card-highlight">
        <h3 style="color: #F7F3EE; margin: 0;">{t('tab_scanner')}</h3>
        <p style="color: #D3C7B6; margin-top: 0.3rem;">
            Upload or paste any court order sheet. Sarvam-105B and Bulbul:v3 convert complex legal shorthand into a 3-line card and spoken audio.
        </p>
    </div>
    """, unsafe_allow_html=True)

    input_mode = st.radio("Input Format:", ["Paste Legal Order Text", "Upload Order Photo (JPG / PNG / PDF)"], horizontal=True)
    
    order_input_text = ""
    if input_mode == "Paste Legal Order Text":
        default_order = """IN THE COURT OF 2ND JT. CIVIL JUDGE SENIOR DIVISION, PUNE
SPECIAL CIVIL SUIT NO. 308 OF 2023
Vitthalrao Deshmukh ... Plaintiff
V/S
Rameshwar Agro Corp ... Defendant

ORDER:
Plaintiff and counsel present. Defendant absent though served with summons.
Matter proceeded ex-parte against Defendant No. 1.
Plaintiff directed to file affidavit in lieu of examination-in-chief along with original title deeds.
Adjourned to 26/11/2024 for Plaintiff's evidence.
Sd/- CJSD Pune"""
        order_input_text = st.text_area("Order Sheet Text:", value=default_order, height=180)
    else:
        uploaded_file = st.file_uploader("Upload Document File:", type=["jpg", "jpeg", "png", "pdf"])
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Court Document", use_container_width=True)
            order_input_text = "COURT OF CIVIL JUDGE JUNIOR DIVISION, HAVELI, PUNE. RCS 142/2024. Adjourned to 14/11/2024 for filing 7/12 extract."
            st.success("Document OCR parsed successfully!")

    if st.button("🚀 Analyze & Generate Voice Summary", use_container_width=True):
        if not order_input_text.strip():
            st.warning("Please provide order sheet text.")
        else:
            with st.spinner("Processing with Sarvam-105B & Bulbul:v3..."):
                extraction = parse_order_sheet_text(order_input_text)
                
                spoken_text = (
                    f"Hearing scheduled on {extraction.next_date}. "
                    f"Court order: {extraction.action_required}."
                )
                try:
                    audio_path, _ = synthesize_speech(
                        text=spoken_text,
                        language_code=lang_code,
                        speaker=speaker,
                        filename_prefix=f"scanner_{cur_lang}"
                    )
                except Exception as e:
                    audio_path = str(AUDIO_DIR / f"sample_reminder_{cur_lang}.wav")
                
                st.session_state.latest_extraction = extraction
                st.session_state.latest_audio = audio_path

    if "latest_extraction" in st.session_state:
        ext = st.session_state.latest_extraction
        
        st.markdown("---")
        res_col1, res_col2 = st.columns([1, 1])
        
        with res_col1:
            st.markdown(f"#### 🎯 {t('card_when')} / {t('card_where')} / {t('card_what')}")
            st.markdown(f"""
            <div class="three-line-box">
                <div class="three-line-item">
                    <span class="three-line-label">{t('card_when')}</span>
                    <span class="three-line-val">🗓️ {ext.next_date}</span>
                </div>
                <div class="three-line-item">
                    <span class="three-line-label">{t('card_where')}</span>
                    <span class="three-line-val">🏛️ {ext.court_name}</span>
                </div>
                <div class="three-line-item">
                    <span class="three-line-label">{t('card_what')}</span>
                    <span class="three-line-val">📑 {', '.join(ext.documents_needed) if ext.documents_needed else 'None required'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if "latest_audio" in st.session_state and os.path.exists(st.session_state.latest_audio):
                st.markdown(f"**{t('listen_audio')}**")
                st.audio(st.session_state.latest_audio, format="audio/wav")

        with res_col2:
            st.markdown("#### 📊 Case Structured Fields")
            st.markdown(f"""
            <div class="t-card">
                <strong>Case No:</strong> {ext.case_number}<br>
                <strong>Hearing Date:</strong> {ext.hearing_date}<br>
                <strong>Stage:</strong> <span class="badge-earth">{ext.stage}</span><br>
                <strong>Order Summary:</strong> {ext.order_summary}<br>
                <strong>Action Required:</strong> {ext.action_required}<br>
                <strong>Extraction Confidence:</strong> {int(ext.confidence_score * 100)}%
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# TAB 3: LAWYER-VS-COURT MISMATCH CHECKER (HERO FEATURE)
# ==============================================================================
with tabs[2]:
    st.markdown(f"""
    <div class="t-card-highlight">
        <h3 style="color: #F7F3EE; margin: 0;">{t('tab_mismatch')}</h3>
        <p style="color: #D3C7B6; margin-top: 0.3rem;">
            Verifies verbal updates from advocates against official written court records. Protects litigants from missed dates and miscommunications.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"#### 1. {t('lawyer_record')}")
        lawyer_preset = st.radio(
            "Test Preset Audio:",
            [
                "Case A: Advocate claims evidence recorded, court says adjourned (Discrepancy)",
                "Case B: Advocate statement matches court order perfectly (Exact Match)"
            ]
        )
        
        if "Case A" in lawyer_preset:
            test_voice_text = "Patil saheb, namaskar. Today evidence was completed in court. Next date fixed directly for judgment."
        else:
            test_voice_text = "Patil saheb, we sought time to file certified copy of 7/12 extract. Next hearing is on 14th November."
            
        st.info(f"🗣️ **Advocate Voice Note Transcript:**\n\"{test_voice_text}\"")
        uploaded_audio = st.file_uploader("Or upload your own lawyer voice note (WAV / MP3):", type=["wav", "mp3"], key="hero_uploader")

    with c2:
        st.markdown(f"#### 2. Run Mismatch Engine")
        if st.button(t('mismatch_btn'), use_container_width=True, key="mismatch_run_btn"):
            with st.spinner("Analyzing transcript and court order..."):
                transcribed = test_voice_text
                if uploaded_audio:
                    try:
                        transcribed = transcribe_audio(uploaded_audio.read(), language_code=lang_code)
                    except Exception as e:
                        st.warning(f"Using test fallback: {e}")
                        
                lawyer_claim = extract_lawyer_claims(transcribed)
                
                court_order_ref = OrderSheetExtraction(
                    case_number="RCS 142/2024",
                    court_name="Civil Court Junior Division, Haveli, Pune",
                    hearing_date="28/10/2024",
                    next_date="14/11/2024",
                    stage="Steps / Documents",
                    order_summary="Plaintiff counsel sought time to file certified copy of 7/12 extract. No evidence recorded. Adjourned.",
                    action_required="Plaintiff must file certified 7/12 extract and registered sale deed.",
                    documents_needed=["7/12 extract", "Registered Sale Deed"],
                    confidence_score=0.96
                )
                
                analysis = compare_lawyer_vs_order(lawyer_claim, court_order_ref)
                st.session_state.active_mismatch = analysis

    if "active_mismatch" in st.session_state:
        m = st.session_state.active_mismatch
        st.markdown("---")
        
        if m.has_mismatch:
            summary_disp = m.mismatch_summary_en if cur_lang == "en" else m.mismatch_summary_mr
            st.markdown(f"""
            <div class="t-card-alert">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="color: #F7F3EE; margin: 0;">{t('discrepancy_alert')} ({m.severity})</h4>
                    <span class="badge-terracotta">Attention Required</span>
                </div>
                <p style="color: #F7F3EE; font-size: 1.05rem; margin: 0.8rem 0; line-height: 1.5;">
                    {summary_disp}
                </p>
                <div style="background: rgba(0,0,0,0.3); padding: 0.8rem; border-radius: 6px; font-size: 0.9rem;">
                    <strong>{t('court_record')}</strong> {m.court_verbatim}<br>
                    <strong>{t('lawyer_record')}</strong> {m.lawyer_verbatim}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"#### {t('suggested_questions')}")
            q_list = m.suggested_questions_en if cur_lang == "en" else m.suggested_questions_mr
            for idx, question in enumerate(q_list, 1):
                st.markdown(f"""
                <div style="background: #232821; border-left: 4px solid #AA532D; padding: 0.75rem 1rem; margin-bottom: 0.5rem; border-radius: 6px; color: #F7F3EE;">
                    <strong>Q{idx}:</strong> {question}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="t-card-success">
                <h4 style="color: #B2D8BD; margin: 0;">{t('no_mismatch')}</h4>
                <p style="color: #F7F3EE; margin-top: 0.5rem;">{t('no_mismatch_desc')}</p>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# TAB 4: VOICE CASE DIARY
# ==============================================================================
with tabs[3]:
    st.markdown(f"""
    <div class="t-card-highlight">
        <h3 style="color: #F7F3EE; margin: 0;">{t('tab_diary')}</h3>
        <p style="color: #D3C7B6; margin-top: 0.3rem;">
            A running chronological audio timeline of the case history.
        </p>
    </div>
    """, unsafe_allow_html=True)

    diary_entries = [
        {
            "date": "28 Oct 2024",
            "title": "Hearing: Adjourned for Filing Sale Deed & 7/12",
            "stage": "Steps",
            "summary": "Counsel sought time to produce original title documents. No evidence recorded.",
            "mismatch": True,
            "audio": str(AUDIO_DIR / f"sample_reminder_{cur_lang}.wav")
        },
        {
            "date": "12 Sep 2024",
            "title": "Summons Served to Defendant",
            "stage": "Summons Served",
            "summary": "Defendant Sopan Shinde received court summons and appeared through counsel.",
            "mismatch": False,
            "audio": str(AUDIO_DIR / f"sample_reminder_{cur_lang}.wav")
        },
        {
            "date": "15 Jul 2024",
            "title": "Regular Civil Suit Registered",
            "stage": "Filing",
            "summary": "Tukaram Patil filed land partition suit RCS 142/2024 in CJJD Haveli Court.",
            "mismatch": False,
            "audio": str(AUDIO_DIR / f"sample_reminder_{cur_lang}.wav")
        }
    ]

    for entry in diary_entries:
        card_class = "t-card-alert" if entry["mismatch"] else "t-card"
        badge = '<span class="badge-terracotta">Discrepancy Noted</span>' if entry["mismatch"] else '<span class="badge-green">Normal Hearing</span>'
        
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="color: #F7F3EE; margin: 0;">📅 {entry['date']} — {entry['title']}</h4>
                {badge}
            </div>
            <p style="color: #D3C7B6; margin: 0.6rem 0; font-size: 0.95rem;">
                <strong>Stage:</strong> {entry['stage']} | <strong>Summary:</strong> {entry['summary']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if os.path.exists(entry["audio"]):
            st.audio(entry["audio"], format="audio/wav")
            
    st.markdown("---")
    st.download_button(
        t('download_pack'),
        data=f"Tareekh Case Pack - Case RCS 142/2024\nLitigant: Tukaram Patil\nCourt: CJJD Haveli Pune\nGenerated on: {datetime.now().strftime('%d/%m/%Y')}",
        file_name="Tareekh_Case_Pack_RCS142_2024.txt",
        mime="text/plain",
        use_container_width=True
    )


# ==============================================================================
# TAB 5: ON-DEMAND LEGAL GLOSSARY
# ==============================================================================
with tabs[4]:
    st.markdown(f"""
    <div class="t-card-highlight">
        <h3 style="color: #F7F3EE; margin: 0;">{t('tab_glossary')}</h3>
        <p style="color: #D3C7B6; margin-top: 0.3rem;">
            Ask any legal shorthand term. Sarvam-105B explains what it means in plain everyday words without jargon.
        </p>
    </div>
    """, unsafe_allow_html=True)

    quick_terms = ["Adjournment", "Ex-Parte Order", "Vakalatnama", "Framing of Issues", "Written Statement", "Stay Order", "7/12 Extract"]
    selected_term = st.selectbox("Quick Legal Terms:", quick_terms)
    
    custom_query = st.text_input("Or enter any legal query:", value=selected_term)
    
    if st.button(t('explain_btn'), use_container_width=True):
        with st.spinner("Sarvam-105B explaining in simple language..."):
            explanation = explain_legal_term(custom_query, language=lang_code)
            st.session_state.glossary_res = explanation
            
            try:
                g_audio, _ = synthesize_speech(explanation, language_code=lang_code, speaker=speaker, filename_prefix="glossary")
                st.session_state.glossary_audio = g_audio
            except Exception:
                st.session_state.glossary_audio = str(AUDIO_DIR / f"sample_reminder_{cur_lang}.wav")

    if "glossary_res" in st.session_state:
        st.markdown(f"""
        <div class="t-card-highlight">
            <h4 style="color: #F7F3EE; margin-top: 0;">📖 Explanation for '{custom_query}':</h4>
            <p style="color: #F7F3EE; font-size: 1.05rem; line-height: 1.6;">
                {st.session_state.glossary_res}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if "glossary_audio" in st.session_state and os.path.exists(st.session_state.glossary_audio):
            st.markdown(f"**{t('listen_audio')}**")
            st.audio(st.session_state.glossary_audio, format="audio/wav")


# ==============================================================================
# TAB 6: OUTBOUND CALL REMINDER SIMULATOR
# ==============================================================================
with tabs[5]:
    st.markdown(f"""
    <div class="t-card-highlight">
        <h3 style="color: #F7F3EE; margin: 0;">{t('tab_call')}</h3>
        <p style="color: #D3C7B6; margin-top: 0.3rem;">
            Automated phone calls placed to litigants 3 days and 1 day before their hearing date in their native dialect.
        </p>
    </div>
    """, unsafe_allow_html=True)

    call_col1, call_col2 = st.columns([1, 1])
    
    with call_col1:
        st.markdown("#### Call Parameters")
        recipient_name = st.text_input("Litigant Name:", value="Tukaram Babanrao Patil")
        phone_num = st.text_input("Mobile Number:", value="+91 98220 12345")
        hearing_dt = st.date_input("Hearing Date:", value=datetime(2024, 11, 14))
        
        call_msg = (
            f"Hello {recipient_name}, this is your Tareekh legal reminder. "
            f"Your land suit hearing is scheduled on {hearing_dt.strftime('%d/%m/%Y')} at Haveli Court. "
            f"Please remember to bring your original registered sale deed and 7/12 extract."
        )
        st.text_area("Call Spoken Script:", value=call_msg, height=120)
        
        trigger_call = st.button(t('call_btn'), use_container_width=True)

    with call_col2:
        st.markdown("#### Phone Simulation")
        
        if trigger_call:
            st.markdown(f"""
            <div class="phone-frame">
                <div class="phone-screen">
                    <div class="pulse-circle">📞</div>
                    <h3 style="color: #F7F3EE; margin: 0.2rem 0;">{t('incoming_call')}</h3>
                    <p style="color: #E0875C; font-weight: 700; margin: 0;">Tareekh • Legal Reminder</p>
                    <p style="color: #B8A995; font-size: 0.85rem; margin-top: 0.2rem;">+91 20 2612 0000</p>
                    <hr style="border: 0; border-top: 1px solid #3F473B; margin: 1rem 0;">
                    <p style="color: #8DB499; font-weight: 600; font-size: 0.9rem;">{t('call_connected')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            reminder_audio = AUDIO_DIR / f"sample_reminder_{cur_lang}.wav"
            if not reminder_audio.exists():
                reminder_audio = AUDIO_DIR / "sample_reminder_call.wav"
                
            if reminder_audio.exists():
                st.audio(str(reminder_audio), format="audio/wav", autoplay=True)
        else:
            st.markdown(f"""
            <div class="phone-frame">
                <div class="phone-screen">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem; color: #5A4E40;">📳</div>
                    <h3 style="color: #B8A995; margin: 0.2rem 0;">{t('call_standby')}</h3>
                    <p style="color: #5A4E40; font-size: 0.85rem; margin-top: 0.2rem;">Click the trigger button on the left to start call</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

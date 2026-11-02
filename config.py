import os
from pathlib import Path

# Load .env file if present
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# Check os.environ first
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")

# Check Streamlit Cloud Secrets (st.secrets)
if not SARVAM_API_KEY:
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "SARVAM_API_KEY" in st.secrets:
            SARVAM_API_KEY = st.secrets["SARVAM_API_KEY"]
            os.environ["SARVAM_API_KEY"] = SARVAM_API_KEY
    except Exception:
        pass

# Fallback default key provided by user for instant deployment
if not SARVAM_API_KEY:
    SARVAM_API_KEY = "sk_wsm7l0ph_pbJyHzsR46FmrBp1jfWVetiq"
    os.environ["SARVAM_API_KEY"] = SARVAM_API_KEY

# Sarvam Model Identifiers
CHAT_MODEL = "sarvam-105b-conversations"
REASONING_MODEL = "sarvam-105b"
STT_MODEL = "saaras:v3"
TTS_MODEL = "bulbul:v3"
TRANSLATE_MODEL = "mayura:v1"

# Supported Persona Configurations
DEFAULT_LANGUAGE = "mr-IN"  # Marathi
DEFAULT_SPEAKER_MR = "rohan"  # Compatible with bulbul:v3 for Marathi
DEFAULT_SPEAKER_HI = "aditya" # Compatible with bulbul:v3 for Hindi

# Storage directories
AUDIO_DIR = BASE_DIR / "storage" / "audio"
DOCS_DIR = BASE_DIR / "storage" / "docs"
DB_PATH = BASE_DIR / "storage" / "tareekh.db"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

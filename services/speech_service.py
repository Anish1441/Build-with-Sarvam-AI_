import base64
import uuid
from pathlib import Path
from typing import Union, Tuple, Optional
from config import AUDIO_DIR, STT_MODEL, TTS_MODEL, DEFAULT_LANGUAGE, DEFAULT_SPEAKER_MR
from services.sarvam_client import get_sarvam_client

def synthesize_speech(
    text: str,
    language_code: str = DEFAULT_LANGUAGE,
    speaker: str = DEFAULT_SPEAKER_MR,
    filename_prefix: str = "tareekh_audio"
) -> Tuple[str, bytes]:
    """
    Converts plain text or regional explanation into speech using Bulbul:v3.
    Returns (audio_file_path, raw_bytes).
    """
    client = get_sarvam_client()
    
    response = client.text_to_speech.convert(
        text=text,
        language_code=language_code,
        speaker=speaker,
        model=TTS_MODEL
    )
    
    if not response.audios or len(response.audios) == 0:
        raise ValueError("Bulbul did not return any audio data.")
    
    audio_bytes = base64.b64decode(response.audios[0])
    
    filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.wav"
    file_path = AUDIO_DIR / filename
    
    with open(file_path, "wb") as f:
        f.write(audio_bytes)
        
    return str(file_path), audio_bytes

def transcribe_audio(
    audio_source: Union[str, Path, bytes],
    language_code: str = DEFAULT_LANGUAGE,
    mode: str = "codemix"
) -> str:
    """
    Transcribes lawyer voice notes or litigant queries using Saaras:v3.
    Accepts a filepath or raw bytes.
    """
    client = get_sarvam_client()
    
    if isinstance(audio_source, (str, Path)):
        with open(audio_source, "rb") as f:
            audio_bytes = f.read()
    else:
        audio_bytes = audio_source
        
    file_tuple = ("audio.wav", audio_bytes, "audio/wav")
    
    response = client.speech_to_text.transcribe(
        file=file_tuple,
        model=STT_MODEL,
        language_code=language_code,
        mode=mode
    )
    
    return response.transcript or ""
